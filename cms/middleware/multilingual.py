from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.conf import settings
from cms.utils.i18n import get_default_language
import re    
from cms import settings as cms_settings

SUB = re.compile(ur'<a([^>]+)href="/(?!(%s|%s|%s))([^"]*)"([^>]*)>' % (
    "|".join(map(lambda l: l[0] + "/" , cms_settings.CMS_LANGUAGES)), 
    settings.MEDIA_URL[1:], 
    settings.ADMIN_MEDIA_PREFIX[1:]
))

SUB2 = re.compile(ur'<form([^>]+)action="/(?!(%s|%s|%s))([^"]*)"([^>]*)>' % (
    "|".join(map(lambda l: l[0] + "/" , cms_settings.CMS_LANGUAGES)),
     settings.MEDIA_URL[1:],
     settings.ADMIN_MEDIA_PREFIX[1:]
))

SUPPORTED = dict(cms_settings.CMS_LANGUAGES)

START_SUB = re.compile(r"^/(%s)/.*" % "|".join(map(lambda l: l[0], cms_settings.CMS_LANGUAGES)))

def has_lang_prefix(path):
    check = START_SUB.match(path)
    if check is not None:
        return check.group(1)
    else:
        return False

class MultilingualURLMiddleware:
    def get_language_from_request (self,request):
        changed = False
        prefix = has_lang_prefix(request.path_info)
        if prefix:
            request.path = "/" + "/".join(request.path.split("/")[2:])
            request.path_info = "/" + "/".join(request.path_info.split("/")[2:]) 
            t = prefix
            if t in SUPPORTED:
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
                if lang in SUPPORTED and lang is not None:
                    return lang
            elif "django_language" in request.COOKIES.keys():
                lang = request.COOKIES.get("django_language", None)
                if lang in SUPPORTED and lang is not None:
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
        path = unicode(request.path)
        if not path.startswith(settings.MEDIA_URL) and \
                not path.startswith(settings.ADMIN_MEDIA_PREFIX) and \
                response.status_code == 200 and \
                response._headers['content-type'][1].split(';')[0] == "text/html":
            response.content = SUB.sub(ur'<a\1href="/%s/\3"\4>' % request.LANGUAGE_CODE, response.content.decode('utf-8'))
            response.content = SUB2.sub(ur'<form\1action="/%s/\3"\4>' % request.LANGUAGE_CODE, response.content.decode('utf-8'))
        if (response.status_code == 301 or response.status_code == 302 ):
            location = response._headers['location']
            prefix = has_lang_prefix(location[1])
            if not prefix and location[1].startswith("/") and \
                    not location[1].startswith(settings.MEDIA_URL) and \
                    not location[1].startswith(settings.ADMIN_MEDIA_PREFIX):
                response._headers['location'] = (location[0], "/%s%s" % (request.LANGUAGE_CODE, location[1]))
        return response
