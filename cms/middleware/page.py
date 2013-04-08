# -*- coding: utf-8 -*-
from cms.appresolver import applications_page_check
from cms.apphook_pool import apphook_pool


class LazyPage(object):
    def __get__(self, request, obj_type=None):
        from cms.utils.page_resolver import get_page_from_request
        if not hasattr(request, '_current_page_cache'):
            request._current_page_cache = get_page_from_request(request)
            if not request._current_page_cache:
                # if this is in a apphook
                # find the page the apphook is attached to
                request._current_page_cache = applications_page_check(request)
        return request._current_page_cache

class LazyPageApp(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_current_app_cache'):
            page = request.current_page
            app_urls = page.get_application_urls()
            if app_urls:
                app = apphook_pool.get_apphook(app_urls)
                request._current_app_cache = page.reverse_id if page.reverse_id else app.app_name
        return request._current_app_cache

class CurrentPageMiddleware(object):
    def process_request(self, request):
        request.__class__.current_page = LazyPage()
        request.__class__.current_app = LazyPageApp()
        return None
