import re
import urllib
from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.conf import settings
from cms.utils.i18n import get_default_language

SUB = re.compile(ur'<a([^>]+)href="/(?=%s)(?!(%s|%s|%s))(%s([^"]*))"([^>]*)>' % (
    urllib.quote(settings.CMS_ROOT[1:]),
    "|".join(map(lambda l: urllib.quote(settings.CMS_ROOT[1:]) + "/" + l[0] + "/" , settings.CMS_LANGUAGES)),
    settings.MEDIA_URL[1:],
    settings.ADMIN_MEDIA_PREFIX[1:],
    urllib.quote(settings.CMS_ROOT[1:])
))

SUB2 = re.compile(ur'<form([^>]+)action="/(?=%s)(?!(%s|%s|%s))(%s([^"]*))"([^>]*)>' % (
    settings.CMS_ROOT[1:],
    "|".join(map(lambda l: settings.CMS_ROOT[1:] + "/" + l[0] + "/" , settings.CMS_LANGUAGES)),
    settings.MEDIA_URL[1:],
    settings.ADMIN_MEDIA_PREFIX[1:],
    settings.CMS_ROOT[1:]
))

SUPPORTED = dict(settings.CMS_LANGUAGES)

START_SUB = re.compile(r"^/(%s)/.*" % "|".join(map(lambda l: l[0], settings.CMS_LANGUAGES)))

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
            request.path = request.path.split("/")
            del request.path[settings.CMS_ROOT.count('/')+1]
            request.path = "/".join(request.path)
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
            try:
                decoded_response = response.content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_response = response.content
            decoded_response = SUB.sub(ur'<a\1href="%s/%s\4"\5>' % (settings.CMS_ROOT, request.LANGUAGE_CODE), decoded_response)
            response.content = SUB2.sub(ur'<form\1action="%s/%s\4"\5>' % (settings.CMS_ROOT, request.LANGUAGE_CODE), decoded_response).encode("utf8")
        if (response.status_code == 301 or response.status_code == 302 ):
            location = response._headers['location']
            prefix = has_lang_prefix(location[1])
            if not prefix and location[1].startswith("/") and \
                    not location[1].startswith(settings.MEDIA_URL) and \
                    not location[1].startswith(settings.ADMIN_MEDIA_PREFIX):
                response._headers['location'] = (location[0], "%s/%s%s" % (settings.CMS_ROOT, request.LANGUAGE_CODE, request.path_info))
        return response
