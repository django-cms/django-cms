from urllib.parse import unquote

from classytags.arguments import Argument, IntegerArgument, StringArgument
from classytags.core import Options
from classytags.helpers import InclusionTag
from django import template
from django.contrib.sites.models import Site
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import force_str
from django.utils.translation import get_language, gettext

from cms.utils.i18n import (
    force_language,
    get_language_list,
    get_language_object,
    get_public_languages,
)
from menus.menu_pool import menu_pool
from menus.utils import DefaultLanguageChanger

register = template.Library()


class NOT_PROVIDED:
    pass


def cut_after(node, levels, removed):
    """
    given a tree of nodes cuts after N levels
    """
    if levels == 0:
        removed.extend(node.children)
        node.children = []
    else:
        removed_local = []
        for child in node.children:
            if child.visible:
                cut_after(child, levels - 1, removed)
            else:
                removed_local.append(child)
        for removed_child in removed_local:
            node.children.remove(removed_child)
        removed.extend(removed_local)


def remove(node, removed):
    removed.append(node)
    if node.parent:
        if node in node.parent.children:
            node.parent.children.remove(node)


def cut_levels(nodes, from_level, to_level, extra_inactive, extra_active):
    """
    cutting nodes away from menus
    """
    final = []
    removed = []
    selected = None
    for node in nodes:
        if not hasattr(node, 'level'):
            # remove and ignore nodes that don't have level information
            remove(node, removed)
            continue
        if node.level == from_level:
            # turn nodes that are on from_level into root nodes
            final.append(node)
            node.parent = None
        if not node.ancestor and not node.selected and not node.descendant:
            # cut inactive nodes to extra_inactive, but not of descendants of
            # the selected node
            cut_after(node, extra_inactive, removed)
        if node.level > to_level and node.parent:
            # remove nodes that are too deep, but not nodes that are on
            # from_level (local root nodes)
            remove(node, removed)
        if node.selected:
            selected = node
        if not node.visible:
            remove(node, removed)
    if selected:
        cut_after(selected, extra_active, removed)
    if removed:
        for node in removed:
            if node in final:
                final.remove(node)
    return final


def flatten(nodes):
    flat = []
    for node in nodes:
        flat.append(node)
        flat.extend(flatten(node.children))
    return flat


@register.tag(name="show_menu")
class ShowMenu(InclusionTag):
    """
    render a nested list of all children of the pages
    - from_level: starting level
    - to_level: max level
    - extra_inactive: how many levels should be rendered of the not active tree?
    - extra_active: how deep should the children of the active node be rendered?
    - namespace: the namespace of the menu. if empty will use all namespaces
    - root_id: the id of the root node
    - template: template used to render the menu
    """
    name = 'show_menu'
    template = 'menu/dummy.html'

    options = Options(
        IntegerArgument('from_level', default=0, required=False),
        IntegerArgument('to_level', default=100, required=False),
        IntegerArgument('extra_inactive', default=0, required=False),
        IntegerArgument('extra_active', default=1000, required=False),
        StringArgument('template', default='menu/menu.html', required=False),
        StringArgument('namespace', default=None, required=False),
        StringArgument('root_id', default=None, required=False),
        Argument('next_page', default=None, required=False),
    )

    def get_context(self, context, from_level, to_level, extra_inactive,
                    extra_active, template, namespace, root_id, next_page):
        try:
            # If there's an exception (500), default context_processors may not be called.
            request = context['request']
        except KeyError:
            return {'template': 'menu/empty.html'}

        if next_page:
            children = next_page.children
        else:
            # new menu... get all the data so we can save a lot of queries
            menu_renderer = context.get('cms_menu_renderer')

            if not menu_renderer:
                menu_renderer = menu_pool.get_renderer(request)

            nodes = menu_renderer.get_nodes(namespace, root_id)
            if root_id:  # find the root id and cut the nodes
                id_nodes = menu_pool.get_nodes_by_attribute(nodes, "reverse_id", root_id)
                if id_nodes:
                    node = id_nodes[0]
                    nodes = node.children
                    for remove_parent in nodes:
                        remove_parent.parent = None
                    from_level += node.level + 1
                    to_level += node.level + 1
                    nodes = flatten(nodes)
                else:
                    nodes = []
            children = cut_levels(nodes, from_level, to_level, extra_inactive, extra_active)
            children = menu_renderer.apply_modifiers(children, namespace, root_id, post_cut=True)

        try:
            context['children'] = children
            context['template'] = template
            context['from_level'] = from_level
            context['to_level'] = to_level
            context['extra_inactive'] = extra_inactive
            context['extra_active'] = extra_active
            context['namespace'] = namespace
        except:  # NOQA
            context = {"template": template}
        return context


@register.tag(name="show_menu_below_id")
class ShowMenuBelowId(ShowMenu):
    name = 'show_menu_below_id'
    options = Options(
        Argument('root_id', default=None, required=False),
        IntegerArgument('from_level', default=0, required=False),
        IntegerArgument('to_level', default=100, required=False),
        IntegerArgument('extra_inactive', default=0, required=False),
        IntegerArgument('extra_active', default=1000, required=False),
        Argument('template', default='menu/menu.html', required=False),
        Argument('namespace', default=None, required=False),
        Argument('next_page', default=None, required=False),
    )


@register.tag(name="show_sub_menu")
class ShowSubMenu(InclusionTag):
    """
    show the sub menu of the current nav-node.
    - levels: how many levels deep
    - root_level: the level to start the menu at
    - nephews: the level of descendants of siblings (nephews) to show
    - template: template used to render the navigation
    """
    name = 'show_sub_menu'
    template = 'menu/dummy.html'

    options = Options(
        IntegerArgument('levels', default=100, required=False),
        Argument('root_level', default=None, required=False),
        IntegerArgument('nephews', default=100, required=False),
        Argument('template', default='menu/sub_menu.html', required=False),
    )

    def get_context(self, context, levels, root_level, nephews, template):
        # Django 1.4 doesn't accept 'None' as a tag value and resolve to ''
        # So we need to force it to None again
        if not root_level and root_level != 0:
            root_level = None
        try:
            # If there's an exception (500), default context_processors may not be called.
            request = context['request']
        except KeyError:
            return {'template': 'menu/empty.html'}

        menu_renderer = context.get('cms_menu_renderer')

        if not menu_renderer:
            menu_renderer = menu_pool.get_renderer(request)

        nodes = menu_renderer.get_nodes()
        children = []
        # adjust root_level so we cut before the specified level, not after
        include_root = False
        if root_level is not None and root_level > 0:
            root_level -= 1
        elif root_level is not None and root_level == 0:
            include_root = True
        for node in nodes:
            if root_level is None:
                if node.selected:
                    # if no root_level specified, set it to the selected nodes level
                    root_level = node.level
                    # is this the ancestor of current selected node at the root level?
            is_root_ancestor = (node.ancestor and node.level == root_level)
            # is a node selected on the root_level specified
            root_selected = (node.selected and node.level == root_level)
            if is_root_ancestor or root_selected:
                cut_after(node, levels, [])
                children = node.children
                for child in children:
                    if child.sibling:
                        cut_after(child, nephews, [])
                        # if root_level was 0 we need to give the menu the entire tree
                    # not just the children
                if include_root:
                    children = menu_renderer.apply_modifiers([node], post_cut=True)
                else:
                    children = menu_renderer.apply_modifiers(children, post_cut=True)
        context['children'] = children
        context['template'] = template
        context['from_level'] = 0
        context['to_level'] = 0
        context['extra_inactive'] = 0
        context['extra_active'] = 0
        return context


@register.tag(name="show_breadcrumb")
class ShowBreadcrumb(InclusionTag):
    """
    Shows the breadcrumb from the node that has the same url as the current request

    - start level: after which level should the breadcrumb start? 0=home
    - template: template used to render the breadcrumb
    """
    name = 'show_breadcrumb'
    template = 'menu/dummy.html'

    options = Options(
        Argument('start_level', default=0, required=False),
        Argument('template', default='menu/breadcrumb.html', required=False),
        Argument('only_visible', default=True, required=False),
    )

    def get_context(self, context, start_level, template, only_visible):
        try:
            # If there's an exception (500), default context_processors may not be called.
            request = context['request']
        except KeyError:
            return {'template': 'cms/content.html'}
        if not (isinstance(start_level, int) or start_level.isdigit()):
            only_visible = template
            template = start_level
            start_level = 0
        try:
            only_visible = bool(int(only_visible))
        except:  # NOQA
            only_visible = bool(only_visible)
        ancestors = []

        menu_renderer = context.get('cms_menu_renderer')

        if not menu_renderer:
            menu_renderer = menu_pool.get_renderer(request)

        nodes = menu_renderer.get_nodes(breadcrumb=True)

        # Find home
        home = None
        root_url = unquote(reverse("pages-root"))
        home = next((node for node in nodes if node.get_absolute_url() == root_url), None)

        # Find selected
        selected = None
        selected = next((node for node in nodes if node.selected), None)

        if selected and selected != home:
            node = selected
            while node:
                if node.visible or not only_visible:
                    ancestors.append(node)
                node = node.parent
        if not ancestors or (ancestors and ancestors[-1] != home) and home:
            ancestors.append(home)
        ancestors.reverse()
        if len(ancestors) >= start_level:
            ancestors = ancestors[start_level:]
        else:
            ancestors = []
        context['ancestors'] = ancestors
        context['template'] = template
        return context


def _raw_language_marker(language, lang_code):
    return language


def _native_language_marker(language, lang_code):
    with force_language(lang_code):
        return force_str(gettext(language))


def _current_language_marker(language, lang_code):
    return force_str(gettext(language))


def _short_language_marker(language, lang_code):
    return lang_code


MARKERS = {
    'raw': _raw_language_marker,
    'native': _native_language_marker,
    'current': _current_language_marker,
    'short': _short_language_marker,
}


@register.tag(name="language_chooser")
class LanguageChooser(InclusionTag):
    """
    Displays a language chooser
    - template: template used to render the language chooser
    """
    name = 'language_chooser'
    template = 'menu/dummy.html'

    options = Options(
        Argument('template', default=NOT_PROVIDED, required=False),
        Argument('i18n_mode', default='raw', required=False),
    )

    def get_context(self, context, template, i18n_mode):
        if template in MARKERS:
            _tmp = template
            if i18n_mode not in MARKERS:
                template = i18n_mode
            else:
                template = NOT_PROVIDED
            i18n_mode = _tmp
        if template is NOT_PROVIDED:
            template = "menu/language_chooser.html"
        if i18n_mode not in MARKERS:
            i18n_mode = 'raw'
        if 'request' not in context:
            # If there's an exception (500), default context_processors may not be called.
            return {'template': 'cms/content.html'}
        marker = MARKERS[i18n_mode]
        current_lang = get_language()
        site = Site.objects.get_current()
        request = context['request']

        if request.user.is_staff:
            languages = get_language_list(site_id=site.pk)
        else:
            languages = get_public_languages(site_id=site.pk)

        languages_info = []

        for language in languages:
            obj = get_language_object(language, site_id=site.pk)
            languages_info.append((obj['code'], marker(obj['name'], obj['code'])))

        context['languages'] = languages_info
        context['current_language'] = current_lang
        context['template'] = template
        return context


@register.tag(name="page_language_url")
class PageLanguageUrl(InclusionTag):
    """
    Displays the url of the current page in the defined language.
    You can set a language_changer function with the set_language_changer function in the utils.py if there is no page.
    This is needed if you have slugs in more than one language.
    """
    name = 'page_language_url'
    template = 'cms/content.html'

    options = Options(
        Argument('lang'),
    )

    def get_context(self, context, lang):
        try:
            # If there's an exception (500), default context_processors may not be called.
            request = context['request']
        except KeyError:
            return {'template': 'cms/content.html'}
        if hasattr(request, "_language_changer"):
            try:
                url = request._language_changer(lang)
            except NoReverseMatch:
                url = DefaultLanguageChanger(request)(lang)
        else:
            # use the default language changer
            url = DefaultLanguageChanger(request)(lang)
        return {'content': url}
