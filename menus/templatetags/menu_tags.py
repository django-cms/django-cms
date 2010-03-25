from menus.menu_pool import menu_pool
from django import template
from django.conf import settings
from cms.utils import get_language_from_request

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

def cut_levels(nodes, from_level, to_level, extra_inactive, extra_active):
    """
    cutting nodes away from menus
    """
    final = []
    removed = []
    selected = None
    for node in nodes: 
        if not node.parent and not node.ancestor and not node.selected:
            cut_after(node, extra_inactive, removed)
        if node.level == from_level:
            final.append(node)
            node.parent = None
        if node.level > to_level and node.parent:
            if node in node.parent.children:
                node.parent.children.remove(node)
        if node.selected:
            selected = node
        if not node.visible:
            removed.append(node)
            if node.parent:
                if node in node.parent.children:
                    node.parent.children.remove(node)
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
show_menu = register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu)


def show_menu_below_id(context, root_id=None, from_level=0, to_level=100, extra_inactive=100, extra_active=100, template_file="menu/menu.html", namespace=None, next_page=None):
    """
    displays a menu below a node that has an uid
    """
    return show_menu(context, from_level, to_level, extra_inactive, extra_active, template_file, root_id=root_id, namespace=namespace, next_page=next_page)
register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu_below_id)


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
    
    
show_sub_menu = register.inclusion_tag('cms/dummy.html',
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
show_breadcrumb = register.inclusion_tag('cms/dummy.html',
                                         takes_context=True)(show_breadcrumb)


def language_chooser(context, template="menu/language_chooser.html"):
    """
    Displays a language chooser
    - template: template used to render the language chooser
    """
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    languages = []
    cms_languages = dict(settings.CMS_LANGUAGES)
    for lang in settings.CMS_FRONTEND_LANGUAGES:
        if lang in cms_languages:
            languages.append((lang, cms_languages[lang]))
    lang = get_language_from_request(request, request.current_page)
    context.update({
        'languages':languages,
        'current_language':lang,
        'template':template,
    })
    return context
language_chooser = register.inclusion_tag('cms/dummy.html', takes_context=True)(language_chooser)


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
