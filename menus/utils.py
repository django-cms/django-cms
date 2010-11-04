from cms.models.titlemodels import Title
from django.conf import settings


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
        reverse('product_view', args=[self.get_slug(language=language)])
        
    Use this function in your nav extender views that have i18n slugs.
    """
    request._language_changer = func

def language_changer_decorator(language_changer):
    """
    A decorator wrapper for set_language_changer.
    
        from menus.utils import language_changer_decorator
        
        @language_changer_decorator(function_get_language_changer_url)
        def my_view_function(request, somearg):
            pass
    """
    def _decorator(func):
        def _wrapped(request, *args, **kwargs):
            set_language_changer(request, language_changer)
            return func(request, *args, **kwargs)
        _wrapped.__name__ = func.__name__
        _wrapped.__doc__ = func.__doc__
        return _wrapped
    return _decorator

class _SimpleLanguageChanger(object):
    def __init__(self, request):
        self.request = request
        self._app_path = None
        
    @property
    def app_path(self):
        if self._app_path is None:
            page_path = self.get_page_path(self.request.LANGUAGE_CODE)
            if page_path:
                self._app_path = self.request.path[len(page_path):]
            else:
                self._app_path = self.request.path
        return self._app_path
        
    def __call__(self, lang):
        return '%s%s' % (self.get_page_path(lang), self.app_path)
    
    def get_page_path(self, lang):
        if getattr(self.request, 'current_page'):
            try:
                return self.request.current_page.get_absolute_url(language=lang, fallback=False)
            except Title.DoesNotExist:
                return self.request.current_page.get_absolute_url(language=lang, fallback=True)
            return self.request.current_page.get_absolute_url(language=lang)
        else:
            return ''

def simple_language_changer(func):
    def _wrapped(request, *args, **kwargs):
        set_language_changer(request, _SimpleLanguageChanger(request))
        return func(request, *args, **kwargs)
    _wrapped.__name__ = func.__name__
    _wrapped.__doc__ = func.__doc__
    return _wrapped

    

def handle_navigation_manipulators(navigation_tree, request):
    for handler_function_name, name in settings.CMS_NAVIGATION_MODIFIERS:
        func_name = handler_function_name.split(".")[-1]
        modifier = __import__(".".join(handler_function_name.split(".")[:-1]),(),(),(func_name,))
        handler_func = getattr(modifier, func_name)  
        handler_func(navigation_tree, request)
    return navigation_tree
