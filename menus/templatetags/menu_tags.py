from menus.menu_pool import menu_pool
from django.contrib.sites.models import Site
from django import template
from django.conf import settings
from django.utils.translation import activate, get_language, ugettext
from django.core.cache import cache


class NOT_PROVIDED: pass


def cut_after(node, levels, removed):
    """
    given a tree of nodes cuts after N levels
    """
    if levels == 0:
        removed.extend(node.children)
        node.children = []
    else:
        for n in node.children:
            cut_after(n, levels - 1, removed)

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
register = template.Library()


def show_menu(context, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template="menu/menu.html", namespace=None, root_id=None, next_page=None, ):
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
                new_nodes = node.children
                for n in new_nodes:
                    n.parent = None
                from_level += node.level + 1
                to_level += node.level + 1
            else:
                new_nodes = []
            nodes = new_nodes
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
show_menu = register.inclusion_tag('menu/dummy.html', takes_context=True)(show_menu)


def show_menu_below_id(context, root_id=None, from_level=0, to_level=100, extra_inactive=100, extra_active=100, template_file="menu/menu.html", namespace=None, next_page=None):
    """
    displays a menu below a node that has an uid
    """
    return show_menu(context, from_level, to_level, extra_inactive, extra_active, template_file, root_id=root_id, namespace=namespace, next_page=next_page)
register.inclusion_tag('menu/dummy.html', takes_context=True)(show_menu_below_id)


def show_sub_menu(context, levels=100, template="menu/sub_menu.html"):
    """
    show the sub menu of the current nav-node.
    -levels: how many levels deep
    -temlplate: template used to render the navigation
    """
    
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
    context.update({'children':children,
                    'template':template,
                    'from_level':0,
                    'to_level':0,
                    'extra_inactive':0,
                    'extra_active':0
                    })
    return context        
    
    
show_sub_menu = register.inclusion_tag('menu/dummy.html',
                                       takes_context=True)(show_sub_menu)


def show_breadcrumb(context, start_level=0, template="menu/breadcrumb.html"):
    """
    Shows the breadcrumb from the node that has the same url as the current request
    
    - start level: after which level should the breadcrumb start? 0=home
    - template: template used to render the breadcrumb 
    """
    
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    ancestors = []
    nodes = menu_pool.get_nodes(request, breadcrumb=True)
    selected = None
    home = None
    for node in nodes:
        if node.selected:
            selected = node
        # find home: TODO: maybe home is not on "/"?
        if node.get_absolute_url() == "/":
            home = node
    if selected and selected != home:
        n = selected
        while n:
            if n.visible:
                ancestors.append(n)
            n = n.parent
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
show_breadcrumb = register.inclusion_tag('menu/dummy.html',
                                         takes_context=True)(show_breadcrumb)


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

def language_chooser(context, template=NOT_PROVIDED, i18n_mode='raw'):
    """
    Displays a language chooser
    - template: template used to render the language chooser
    """
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
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    marker = MARKERS[i18n_mode]
    cms_languages = dict(settings.CMS_LANGUAGES)
    current_lang = get_language()
    site = Site.objects.get_current()
    cache_key = '%s-language-chooser-%s-%s-%s' % (settings.CMS_CACHE_PREFIX, site.pk, current_lang, i18n_mode)
    languages = cache.get(cache_key, [])
    if not languages:
        for lang in settings.CMS_FRONTEND_LANGUAGES:
            if lang in cms_languages:
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
language_chooser = register.inclusion_tag('menu/dummy.html', takes_context=True)(language_chooser)


def page_language_url(context, lang):
    """
    Displays the url of the current page in the defined language.
    You can set a language_changer function with the set_language_changer function in the utils.py if there is no page.
    This is needed if you have slugs in more than one language.
    """
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
            return ''
        try:
            from django.core.urlresolvers import reverse
            root = reverse('pages-root')
            url = page.get_absolute_url(language=lang, fallback=False)
            url = root + lang + "/" + url[len(root):] 
        except:
            # no localized path/slug. 
            url = ''
    return {'content':url}
page_language_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_language_url)
