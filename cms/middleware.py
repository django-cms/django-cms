from cms.utils import get_site_from_request, get_page_from_request
from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.conf import settings
import re

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

SUB = re.compile(ur'<a([^>]+)href="/(.*)"([^>].*)>').sub
SUB2 = re.compile(ur'<form([^>]+)action="/(.*)"([^>].*)>').sub

class MultilingualURLMiddleware:
    def get_language_from_request (self,request):
        supported = dict(settings.LANGUAGES)
        lang = settings.LANGUAGE_CODE[:2]
        
        #langs = ""
        #for lang in settings.LANGUAGES:
        #    langs += lang[0]+"|"
        #langs = langs[:-1]
        
        langs = "|".join(map(lambda l: l[0], settings.LANGUAGES))
        check = re.match(r"^/(%s)/.*" % langs, request.path)
        changed = False
        if check is not None:
            request.path = request.path[3:]
            request.path_info = request.path_info[3:]
            t = check.group(1)
            if t in supported:
                lang = t
                if hasattr(request, "session"):
                    request.session["django_language"] = lang
                else:
                    request.set_cookie("django_language", lang)
                changed = True
        else:
            lang = translation.get_language_from_request(request)
        if not changed:
            if hasattr(request, "session"):
                lang = request.session.get("django_language", None)
                if lang in supported and lang is not None:
                    return lang
            elif "django_language" in request.COOKIES.keys():
                lang = request.COOKIES.get("django_language", None)
                if lang in supported and lang is not None:
                    return lang
            if not lang:
                lang = translation.get_language_from_request(request) 
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
        print response._headers['content-type'][1].split(';')[0]
        if response.status_code == 200 and not request.path.startswith(settings.MEDIA_URL) and response._headers['content-type'][1].split(';')[0] == "text/html":
            response.content = \
                SUB(ur'<a\1href="/%s/\2"\3>' % request.LANGUAGE_CODE, \
                    response.content.decode('utf-8'))
            response.content = \
                SUB2(ur'<form\1action="/%s/\2"\3>' % request.LANGUAGE_CODE, \
                    response.content.decode('utf-8'))
        return response