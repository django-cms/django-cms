
from menus.menu_pool import menu_pool
from django import template
from django.conf import settings
from cms.utils import get_language_from_request

def cut_after(node, levels, removed):
    if levels == 0:
        removed.extend(node.children)
        node.children = []
    else:
        for n in node.children:
            cut_after(n, levels - 1, removed)

def cut_levels(nodes, from_level, to_level, extra_inactive, extra_active):
    final = []
    removed = []
    selected = None
    for node in nodes: 
        if not node.parent and not node.ancestor and not node.selected:
            cut_after(node, extra_inactive, removed)
        if node.level == from_level:
            final.append(node)
        if node.level > to_level and node.parent:
            if node in node.parent.children:
                node.parent.children.remove(node)
        if node.selected:
            selected = node
    if selected:
        cut_after(selected, extra_active, removed)
    if removed:
        for node in final:
            if node in removed:
                final.remove(node)
    return final

register = template.Library()

def show_menu(context, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template="menu/menu.html", next_page=None, root_id=None):
    """
    render a nested list of all children of the pages
    from_level: is the start level
    to_level: is the max level rendered

    """
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    
    if next_page:
        children = next_page.children
    else: 
        #new menu... get all the data so we can save a lot of queries
        nodes = menu_pool.get_nodes(request, root_id)
        children = cut_levels(nodes, from_level, to_level, extra_inactive, extra_active)
    context.update({'children':children,
                    'template':template,
                    'from_level':from_level,
                    'to_level':to_level,
                    'extra_inactive':extra_inactive,
                    'extra_active':extra_active})
    return context
show_menu = register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu)

def show_sub_menu(context, levels=100, template="menu/sub_menu.html"):
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    nodes = menu_pool.get_nodes(request)
    children = []
    for node in nodes:
        if node.selected:
            cut_after(node, levels, [])
            children = node.children
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
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    ancestors = []
    nodes = menu_pool.get_nodes(request)
    selected = None
    home = None
    for node in nodes:
        if node.selected:
            selected = node
        print node.get_absolute_url()
        if node.get_absolute_url() == "/":
            home = node
    if selected and selected != home:
        n = selected
        while n:
            ancestors.append(n)
            n = n.parent
    ancestors.append(home)
    ancestors.reverse()
    context.update({'ancestors':ancestors,
                    'template': template})
    return context
show_breadcrumb = register.inclusion_tag('cms/dummy.html',
                                         takes_context=True)(show_breadcrumb)
                                         
                                         
                                         

def language_chooser(context, template="menu/language_chooser.html"):
    """
    Displays a language chooser
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
    if not 'request' in context:
        return ''
    request = context['request']
    if hasattr(request, "_language_changer"):
        url = "/%s" % lang + request._language_changer(lang)
    else:
        page = request.current_page
        if page == "dummy":
            return ''
        try:
            url = "/%s" % lang + page.get_absolute_url(language=lang, fallback=False)
        except:
            url = "/%s/" % lang 
    if url:
        return {'content':url}
    return {'content':''}
page_language_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_language_url)




'''
def show_menu_below_id(context, root_id=None, from_level=0, to_level=100, extra_inactive=100, extra_active=100, template_file="cms/menu.html", next_page=None):
    return show_menu(context, from_level, to_level, extra_inactive, extra_active, template_file, next_page, root_id=root_id)
register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu_below_id)



def page_language_url(context, lang):
    """
    Displays the url of the current page in the defined language.
    You can set a language_changer function with the set_language_changer function in the utils.py if there is no page.
    This is needed if you have slugs in more than one language.
    """
    if not 'request' in context:
        return ''
    
    request = context['request']
    page = request.current_page
    if page == "dummy":
        return ''
    if hasattr(request, "_language_changer"):
        url = "/%s" % lang + request._language_changer(lang)
    else:
        try:
            url = "/%s" % lang + page.get_absolute_url(language=lang, fallback=False)
        except:
            url = "/%s/" % lang 
    if url:
        return {'content':url}
    return {'content':''}
page_language_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_language_url)


def language_chooser(context, template="cms/language_chooser.html"):
    """
    Displays a language chooser
    """
    if not 'request' in context:
        return ''
    
    request = context['request']
    languages = []
    cms_languages = dict(settings.CMS_LANGUAGES)
    for lang in settings.CMS_FRONTEND_LANGUAGES:
        if lang in cms_languages:
            languages.append((lang, cms_languages[lang]))
    lang = get_language_from_request(request, request.current_page)
    context.update(locals())
    return context
language_chooser = register.inclusion_tag('cms/dummy.html', takes_context=True)(language_chooser)
'''