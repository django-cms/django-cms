from cms.utils import get_site_from_request, get_page_from_request
from django.utils.cache import patch_vary_headers
from django.utils import translation


class LazySite(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_site'):
            request._cached_site = get_site_from_request(request)
        return request._cached_site

class CurrentSiteMiddleware(object):
    def process_request(self, request):
        request.__class__.site = LazySite()
        return None
    
class LazyPage(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_current_page_cache'):
            request._current_page_cache = get_page_from_request(request)
        return request._current_page_cache
    
class CurrentPageMiddleware(object):
    def process_request(self, request):
        request.__class__.current_page = LazyPage()
        return None

class MultilingualURLMiddleware:
    def get_language_from_request (self,request):
        from django.conf import settings
        import re
        supported = dict(settings.LANGUAGES)
        lang = settings.LANGUAGE_CODE[:2]
        check = re.match(r"/(\w\w)/.*", request.path)
        changed = False
        if check is not None:
            request.path = request.path[3:]
            print request.path
            t = check.group(1)
            if t in supported:
                lang = t
                if hasattr(request, "session"):
                    request.session["django_language"] = lang
                else:
                    request.set_cookie("django_language", lang)
                changed = True
        if not changed:
            if hasattr(request, "session"):
                lang = request.session.get("django_language", None)
                if lang in supported and lang is not None:
                    return lang
            else:
                lang = request.COOKIES.get("django_language", None)
                if lang in supported and lang is not None:
                    return lang
        return lang
    
    def process_request(self, request):
        from django.conf import settings
        language = self.get_language_from_request(request)
        if language is None:
            language = settings.LANGUAGE_CODE[:2]
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        
    def process_response(self, request, response):
        patch_vary_headers(response, ("Accept-Language",))
        translation.deactivate()
        return response