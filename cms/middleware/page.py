# -*- coding: utf-8 -*-
class LazyPage(object):
    def __get__(self, request, obj_type=None):
        from cms.utils.page_resolver import get_page_from_request
        if not hasattr(request, '_current_page_cache'):
            request._current_page_cache = get_page_from_request(request)
        return request._current_page_cache
    
class CurrentPageMiddleware(object):
    def process_request(self, request):
        request.__class__.current_page = LazyPage()
        return None