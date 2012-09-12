# -*- coding: utf-8 -*-
from classytags.arguments import IntegerArgument, Argument, StringArgument
from classytags.core import Options
from classytags.helpers import InclusionTag
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.translation import activate, get_language, ugettext
from menus.menu_pool import menu_pool
import urllib

register = template.Library()


class NOT_PROVIDED: pass


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
            #new menu... get all the data so we can save a lot of queries
            nodes = menu_pool.get_nodes(request, namespace, root_id)
            if root_id: # find the root id and cut the nodes
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
            children = menu_pool.apply_modifiers(children, request, namespace, root_id, post_cut=True)
    
        try:
            context.update({'children':children,
                            'template':template,
                            'from_level':from_level,
                            'to_level':to_level,
                            'extra_inactive':extra_inactive,
                            'extra_active':extra_active,
                            'namespace':namespace})
        except:
            context = {"template":template}
        return context
register.tag(ShowMenu)


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
register.tag(ShowMenuBelowId)


class ShowSubMenu(InclusionTag):
    """
    show the sub menu of the current nav-node.
    - levels: how many levels deep
    - template: template used to render the navigation
    """
    name = 'show_sub_menu'
    template = 'menu/dummy.html'
    
    options = Options(
        IntegerArgument('levels', default=100, required=False),
        Argument('template', default='menu/sub_menu.html', required=False),
    )
    
    def get_context(self, context, levels, template):
        try:
            # If there's an exception (500), default context_processors may not be called.
            request = context['request']
        except KeyError:
            return {'template': 'menu/empty.html'}
        nodes = menu_pool.get_nodes(request)
        children = []
        for node in nodes:
            if node.selected:
                cut_after(node, levels, [])
                children = node.children
                for child in children:
                    child.parent = None
                children = menu_pool.apply_modifiers(children, request, post_cut=True)
        context.update({
            'children':children,
            'template':template,
            'from_level':0,
            'to_level':0,
            'extra_inactive':0,
            'extra_active':0
        })
        return context        
register.tag(ShowSubMenu)


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
        except:
            only_visible = bool(only_visible)
        ancestors = []
        nodes = menu_pool.get_nodes(request, breadcrumb=True)
        selected = None
        home = None
        for node in nodes:
            if node.selected:
                selected = node
            if node.get_absolute_url() == urllib.unquote(reverse("pages-root")):
                home = node
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
        context.update({'ancestors':ancestors,
                        'template': template})
        return context
register.tag(ShowBreadcrumb)


def _raw_language_marker(language, lang_code):
    return language

def _native_language_marker(language, lang_code):
    activate(lang_code)
    return unicode(ugettext(language))

def _current_language_marker(language, lang_code):
    return unicode(ugettext(language))

def _short_language_marker(language, lang_code):
    return lang_code

MARKERS = {
    'raw': _raw_language_marker,
    'native': _native_language_marker,
    'current': _current_language_marker,
    'short': _short_language_marker,
}

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
        if not i18n_mode in MARKERS:
            i18n_mode = 'raw'
        if 'request' not in context:
            # If there's an exception (500), default context_processors may not be called.
            return {'template': 'cms/content.html'}
        marker = MARKERS[i18n_mode]
        cms_languages = dict(settings.CMS_LANGUAGES)
        current_lang = get_language()
        site = Site.objects.get_current()
        site_languages = settings.CMS_SITE_LANGUAGES.get(site.pk, cms_languages.keys())
        cache_key = '%s-language-chooser-%s-%s-%s' % (settings.CMS_CACHE_PREFIX, site.pk, current_lang, i18n_mode)
        languages = cache.get(cache_key, [])
        if not languages:
            for lang in settings.CMS_FRONTEND_LANGUAGES:
                if lang in cms_languages and lang in site_languages:
                    languages.append((lang, marker(cms_languages[lang], lang)))
            if current_lang != get_language():
                activate(current_lang)
            cache.set(cache_key, languages)
        lang = get_language()
        context.update({
            'languages':languages,
            'current_language':lang,
            'template':template,
        })
        return context
register.tag(LanguageChooser)


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
                setattr(request._language_changer, 'request', request)
            except AttributeError:
                pass
            url = "/%s" % lang + request._language_changer(lang)
        else:
            page = request.current_page
            if page == "dummy":
                return {'content': ''}
            try:
                url = page.get_absolute_url(language=lang, fallback=False)
                url = "/" + lang + url
            except:
                # no localized path/slug
                if settings.CMS_HIDE_UNTRANSLATED:
                    # redirect to root url if CMS_HIDE_UNTRANSLATED
                    url = '/' + lang + '/'
                else:
                    # If untranslated pages are shown, this will not redirect
                    # at all.
                    url = ''
        return {'content':url}
register.tag(PageLanguageUrl)
