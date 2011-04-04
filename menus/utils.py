# -*- coding: utf-8 -*-
from cms.models.titlemodels import Title


def mark_descendants(nodes):
    for node in nodes:
        node.descendant = True
        mark_descendants(node.children)

def cut_levels(nodes, level):
    """
    For cutting the nav_extender levels if you have a from_level in the navigation.
    """
    result = []
    if nodes:
        if nodes[0].level == level:
            return nodes
    for node in nodes:
        result += cut_levels(node.children, level)
    return result

def find_selected(nodes):
    """
    Finds a selected nav_extender node 
    """
    for node in nodes:
        if hasattr(node, "selected"):
            return node
        elif hasattr(node, "ancestor"):
            result = find_selected(node.children)
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
        if getattr(self.request, 'current_page', None):
            try:
                return self.request.current_page.get_absolute_url(language=lang, fallback=False)
            except Title.DoesNotExist:
                return self.request.current_page.get_absolute_url(language=lang, fallback=True)
        else:
            return ''

def simple_language_changer(func):
    def _wrapped(request, *args, **kwargs):
        set_language_changer(request, _SimpleLanguageChanger(request))
        return func(request, *args, **kwargs)
    _wrapped.__name__ = func.__name__
    _wrapped.__doc__ = func.__doc__
    return _wrapped