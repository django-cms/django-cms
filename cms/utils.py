from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from cms import settings
from cms.models import Page

def auto_render(func):
    """Decorator that put automaticaly the template path in the context dictionary
    and call the render_to_response shortcut"""
    def _dec(request, *args, **kwargs):
        t = None
        if kwargs.get('only_context', False):
            # return only context dictionary
            del(kwargs['only_context'])
            response = func(request, *args, **kwargs)
            if isinstance(response, HttpResponse) or isinstance(response, HttpResponseRedirect):
                raise Exception("cannot return context dictionary because a HttpResponseRedirect has been found")
            (template_name, context) = response
            return context
        if "template_name" in kwargs:
            t = kwargs['template_name']
            del kwargs['template_name']
        response = func(request, *args, **kwargs)
        if isinstance(response, HttpResponse) or isinstance(response, HttpResponseRedirect):
            return response
        (template_name, context) = response
        if not t:
            t = template_name
        context['template_name'] = t
        return render_to_response(t, context, context_instance=RequestContext(request))
    return _dec

def get_template_from_request(request, obj=None):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    if len(settings.CMS_TEMPLATES) == 1:
        return settings.CMS_TEMPLATES[0][0]
    template = request.REQUEST.get('template', None)
    if template is not None and template in dict(settings.CMS_TEMPLATES).keys():
        return template
    if obj is not None:
        return obj.get_template()
    return settings.CMS_TEMPLATES[0][0]

def get_language_in_settings(iso):
    for language in settings.CMS_LANGUAGES:
        if language[0][:2] == iso:
            return iso
    return None

def get_language_from_request(request, current_page=None):
    """
    Return the most obvious language according the request
    """
    language = get_language_in_settings(request.REQUEST.get('language', None))
    if language is None:
        language = getattr(request, 'LANGUAGE_CODE', None)
    if language is None:
        # in last resort, get the first language available in the page
        if current_page:
            languages = current_page.get_languages()
            if len(languages) > 0:
                language = languages[0]
    if language is None:
        language = settings.CMS_DEFAULT_LANGUAGE
    return language[:2]

def has_page_add_permission(request, page=None):
    """
    Return true if the current user has permission to add a new page.
    """
    if not settings.CMS_PERMISSION:
        return True
    else:
        from cms.models import PagePermission
        permissions = PagePermission.objects.get_edit_id_list(request.user)
        if permissions == "All":
            return True
        target = request.GET.get('target', -1)
        position = request.GET.get('position', None)
        if int(target) in permissions:
            if position == "first-child":
                return True
            else:
                if Page.objects.get(pk=target).parent_id in permissions:
                    return True
    return False


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


def make_tree(items, levels, url, ancestors, descendants=False, current_level=0, to_levels=100, active_levels=0):
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
        if levels == 0 and not hasattr(item, "ancestor" ) or item.level == to_levels:
            item.childrens = []
        else:
            make_tree(item.childrens, levels, url, ancestors+[item], descendants, current_level, to_levels, active_levels) 
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
        make_tree(items, 100, request.path, ancestors, descendants, current_level, 100, active_levels)
    make_tree(items, levels, request.path, ancestors, descendants, current_level, to_levels, active_levels)
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
        target.selected = True
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
            page.menu_level = target.menu_level + 1
            page.ancestors_ascending = list(target.ancestors_ascending) + [target]
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
    