import re
import urllib
from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.conf import settings
from cms.utils.i18n import get_default_language
from django.core.urlresolvers import reverse

SUPPORTED = dict(settings.CMS_LANGUAGES)

HAS_LANG_PREFIX_RE = re.compile(r"^/(%s)/.*" % "|".join(map(lambda l: l[0], settings.CMS_LANGUAGES)))

def has_lang_prefix(path):
    check = HAS_LANG_PREFIX_RE.match(path)
    if check is not None:
        return check.group(1)
    else:
        return False

class MultilingualURLMiddleware:
    def get_language_from_request (self,request):
        changed = False
        prefix = has_lang_prefix(request.path_info)
        pages_root = urllib.unquote(reverse("pages-root")[:-1])
        if prefix:
            request.path = request.path.split("/")
            del request.path[pages_root.count('/')+1]
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
        pages_root = urllib.unquote(reverse("pages-root")[:-1])

        if not path.startswith(settings.MEDIA_URL) and \
                not path.startswith(settings.ADMIN_MEDIA_PREFIX) and \
                response.status_code == 200 and \
                response._headers['content-type'][1].split(';')[0] == "text/html":
            try:
                decoded_response = response.content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_response = response.content

            # Customarily user pages are served from http://the.server.com/~username/
            # When a user uses django-cms for his pages, the '~' of the url appears
            # quoted in href links. We have to quote pages_root for the regular expression
            # to match.
            HREF_URL_FIX_RE = re.compile(ur'<a([^>]+)href="(?=%s)(?!(%s|%s|%s))(%s([^"]*))"([^>]*)>' % (
                urllib.quote(pages_root),
                "|".join(map(lambda l: urllib.quote(pages_root) + "/" + l[0] + "/" , settings.CMS_LANGUAGES)),
                settings.MEDIA_URL,
                settings.ADMIN_MEDIA_PREFIX,
                urllib.quote(pages_root)
            ))

            # Unlike in href links, the '~' (see above) the '~' in form actions appears
            # unquoted.
            FORM_URL_FIX_RE = re.compile(ur'<form([^>]+)action="(?=%s)(?!(%s|%s|%s))(%s([^"]*))"([^>]*)>' % (
                pages_root,
                "|".join(map(lambda l: pages_root + "/" + l[0] + "/" , settings.CMS_LANGUAGES)),
                settings.MEDIA_URL,
                settings.ADMIN_MEDIA_PREFIX,
                pages_root
            ))

            decoded_response = HREF_URL_FIX_RE.sub(ur'<a\1href="%s/%s\4"\5>' % (pages_root, request.LANGUAGE_CODE), decoded_response)
            response.content = FORM_URL_FIX_RE.sub(ur'<form\1action="%s/%s\4"\5>' % (pages_root, request.LANGUAGE_CODE), decoded_response).encode("utf8")

        if (response.status_code == 301 or response.status_code == 302 ):
            location = response._headers['location']
            prefix = has_lang_prefix(location[1])
            if not prefix and location[1].startswith("/") and \
                    not location[1].startswith(settings.MEDIA_URL) and \
                    not location[1].startswith(settings.ADMIN_MEDIA_PREFIX):
                response._headers['location'] = (location[0], "%s/%s%s" % (pages_root, request.LANGUAGE_CODE, request.path_info))
        return response
