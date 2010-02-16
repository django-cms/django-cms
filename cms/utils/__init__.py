# TODO: this is just stuff from utils.py - should be splitted / moved
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from cms.utils.i18n import get_default_language

# !IMPORTANT: Page cant be imported here, because we will get cyclic import!!

def auto_render(func):
    """Decorator that put automaticaly the template path in the context dictionary
    and call the render_to_response shortcut"""
    def _dec(request, *args, **kwargs):
        t = None
        if kwargs.get('only_context', False):
            # return only context dictionary
            del(kwargs['only_context'])
            response = func(request, *args, **kwargs)
            if isinstance(response, HttpResponseRedirect):
                raise Exception("cannot return context dictionary because a HttpResponseRedirect has been found")
            (template_name, context) = response
            return context
        if "template_name" in kwargs:
            t = kwargs['template_name']
            del kwargs['template_name']
        response = func(request, *args, **kwargs)
        if isinstance(response, HttpResponse):
            return response
        (template_name, context) = response
        if not t:
            t = template_name
        context['template_name'] = t
        return render_to_response(t, context, context_instance=RequestContext(request))
    return _dec

def get_template_from_request(request, obj=None, no_current_page=False):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    template = None
    if len(settings.CMS_TEMPLATES) == 1:
        return settings.CMS_TEMPLATES[0][0]
    if "template" in request.REQUEST:
        template = request.REQUEST['template']
    if not template and obj is not None:
        template = obj.get_template()
    if not template and not no_current_page and hasattr(request, "current_page"):
        current_page = request.current_page
        if hasattr(current_page, "get_template"):
            template = current_page.get_template()
    if template is not None and template in dict(settings.CMS_TEMPLATES).keys():
        if template == settings.CMS_TEMPLATE_INHERITANCE_MAGIC and obj:
            # Happens on admin's request when changing the template for a page
            # to "inherit".
            return obj.get_template()
        return template    
    return settings.CMS_TEMPLATES[0][0]


def get_language_from_request(request, current_page=None):
    from cms.models import Page
    """
    Return the most obvious language according the request
    """
    if settings.CMS_DBGETTEXT: 
        return get_default_language()

    language = request.REQUEST.get('language', None)
    
    if language:
        if not language in dict(settings.CMS_LANGUAGES).keys():
            language = None
        
    if language is None:
        language = getattr(request, 'LANGUAGE_CODE', None)
        
    if language:
        if not language in dict(settings.CMS_LANGUAGES).keys():
            language = None

    # TODO: This smells like a refactoring oversight - was current_page ever a page object? It appears to be a string now
    if language is None and isinstance(current_page, Page):
        # in last resort, get the first language available in the page
        languages = current_page.get_languages()

        if len(languages) > 0:
            language = languages[0]

    if language is None:
        # language must be defined in CMS_LANGUAGES, so check first if there
        # is any language with LANGUAGE_CODE, otherwise try to split it and find
        # best match
        language = get_default_language()

    return language


def get_page_from_request(request):
    """
    tries to get a page from a request if the page hasn't been handled by the cms urls.py
    """
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache
    else:
        path = request.path
        from cms.views import details
        
        kw = {}
        # TODO: very ugly - change required!
        
        if path.startswith('/admin/'):
            kw['page_id']=path.split("/")[0]
        else:
            kw['slug']=path[1:-1]
        resp = details(request, no404=True, only_context=True, **kw)
        return resp['current_page']


def mark_descendants(nodes):
    for node in nodes:
        node.descendant = True
        mark_descendants(node.childrens)

def make_tree(request, items, levels, url, ancestors, descendants=False, current_level=0, to_levels=100, active_levels=0):
    from cms.models import Page
    """
    builds the tree of all the navigation extender nodes and marks them with some metadata
    """
    levels -= 1
    current_level += 1
    found = False
    for item in items:
        item.level = current_level
        if descendants and not found:
            item.descendant = True
        item.ancestors_ascending = ancestors
        if item.get_absolute_url() == url:
            item.selected = True
            item.descendant = False
            levels = active_levels
            descendants = True
            found = True
            last = None
            for anc in ancestors:
                if not isinstance(anc, Page) and last:
                    last = None
                    if hasattr(last, 'childrens'):
                        for child in last.childrens:
                            if isinstance(child, Page):
                                child.sibling = True
                else:
                    last = anc
                anc.ancestor = True
            if last:
                if hasattr(last, 'childrens'):
                    for child in last.childrens:
                        if isinstance(child, Page):
                            child.sibling = True
        elif found:
            item.sibling = True
        if levels == 0 and not hasattr(item, "ancestor" ) or item.level == to_levels or not hasattr(item, "childrens"):
            item.childrens = []
        else:
            make_tree(request, item.childrens, levels, url, ancestors+[item], descendants, current_level, to_levels, active_levels) 
    if found:
        for item in items:
            if not hasattr(item, "selected"):
                item.sibling = True

def get_extended_navigation_nodes(request, levels, ancestors, current_level, to_levels, active_levels, mark_sibling, path):
    """
    discovers all navigation nodes from navigation extenders
    """    
    func_name = path.split(".")[-1]
    ext = __import__(".".join(path.split(".")[:-1]),(),(),(func_name,))
    func = getattr(ext, func_name)
    items = func(request)
    descendants = False
    for anc in ancestors:
        if hasattr(anc, 'selected'):
            if anc.selected:
                descendants = True
    if len(ancestors) and hasattr(ancestors[-1], 'ancestor'):
        make_tree(request, items, 100, request.path, ancestors, descendants, current_level, 100, active_levels)
    make_tree(request, items, levels, request.path, ancestors, descendants, current_level, to_levels, active_levels)
    if mark_sibling:
        for item in items:
            if not hasattr(item, "selected" ):
                item.sibling = True
    return items
    
def find_children(target, pages, levels=100, active_levels=0, ancestors=None, selected_pk=0, soft_roots=True, request=None, no_extended=False, to_levels=100):
    """
    recursive function for marking all children and handling the active and inactive trees with the level limits
    """
    if not hasattr(target, "childrens"):
        target.childrens = []
    if ancestors == None:
        ancestors = []
    if target.pk in ancestors:
        target.ancestor = True
    if target.pk == selected_pk:
        levels = active_levels
    if (levels <= 0 or (target.soft_root and soft_roots)) and not target.pk in ancestors:
        return
    mark_sibling = False 
    for page in pages:
        if page.parent_id and page.parent_id == target.pk:
            if hasattr(target, "selected") or hasattr(target, "descendant"):
                page.descendant = True
            if len(target.childrens):
                target.childrens[-1].last = False
            page.ancestors_ascending = [target] + list(target.ancestors_ascending)
            page.home_pk_cache = target.home_pk_cache
            page.last = True
            target.childrens.append(page)    
            find_children(page, 
                          pages, 
                          levels-1, 
                          active_levels, 
                          ancestors, 
                          selected_pk, 
                          soft_roots, 
                          request, 
                          no_extended,
                          to_levels)
            if hasattr(page, "selected"):
                mark_sibling = True
    if target.navigation_extenders and (levels > 0 or target.pk in ancestors) and not no_extended and target.level < to_levels:
        target.childrens += get_extended_navigation_nodes(request, 
                                                          levels, 
                                                          list(target.ancestors_ascending) + [target], 
                                                          target.level, 
                                                          to_levels,
                                                          active_levels,
                                                          mark_sibling,
                                                          target.navigation_extenders)

def cut_levels(nodes, level):
    """
    For cutting the nav_extender levels if you have a from_level in the navigation.
    """
    result = []
    if nodes:
        if nodes[0].level == level:
            return nodes
    for node in nodes:
        result += cut_levels(node.childrens, level)
    return result

def find_selected(nodes):
    """
    Finds a selected nav_extender node 
    """
    for node in nodes:
        if hasattr(node, "selected"):
            return node
        if hasattr(node, "ancestor"):
            result = find_selected(node.childrens)
            if result:
                return result
            
            
def set_language_changer(request, func):
    """
    
    Sets a language chooser function that accepts one parameter: language
    The function should return a url in the supplied language
    normally you would want to give it the get_absolute_url function with an optional language parameter
    example:
    
    def get_absolute_url(self, language=None):
        reverse("product_view", args=[self.get_slug(language=language)])
        
    Use this function in your nav extender views that have i18n slugs.
    """
    request._language_changer = func