from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.conf import settings
from cms.utils.i18n import get_default_language
import re    

SUB = re.compile(ur'<a([^>]+)href="/(?!(%s|%s|%s))([^"]*)"([^>]*)>' % (
    "|".join(map(lambda l: l[0] + "/" , settings.LANGUAGES)), 
    settings.MEDIA_URL[1:], 
    settings.ADMIN_MEDIA_PREFIX[1:]
))

SUB2 = re.compile(ur'<form([^>]+)action="/(?!(%s|%s|%s))([^"]*)"([^>]*)>' % (
    "|".join(map(lambda l: l[0] + "/" , settings.LANGUAGES)),
     settings.MEDIA_URL[1:],
     settings.ADMIN_MEDIA_PREFIX[1:]
))

class MultilingualURLMiddleware:
    def get_language_from_request (self,request):
        supported = dict(settings.LANGUAGES)
        #lang = settings.LANGUAGE_CODE
        langs = "|".join(map(lambda l: l[0], settings.LANGUAGES))
        check = re.match(r"^/(%s)/.*" % langs, request.path_info)
        changed = False
        if check is not None:
            request.path = "/" + "/".join(request.path.split("/")[2:])
            request.path_info = "/" + "/".join(request.path_info.split("/")[2:]) 
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
        lang = get_default_language(lang)
        return lang
    
    def process_request(self, request):
        language = self.get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        
        
    def process_response(self, request, response):
        patch_vary_headers(response, ("Accept-Language",))
        translation.deactivate()
        if response.status_code == 200 and not request.path.startswith(settings.MEDIA_URL) and response._headers['content-type'][1].split(';')[0] == "text/html":
            response.content = SUB.sub(ur'<a\1href="/%s/\3"\4>' % request.LANGUAGE_CODE, response.content.decode('utf-8'))
            response.content = SUB2.sub(ur'<form\1action="/%s/\3"\4>' % request.LANGUAGE_CODE, response.content.decode('utf-8'))
        return response
