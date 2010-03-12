import re
import urllib
from django.middleware.locale import LocaleMiddleware
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
        pages_root = urllib.unquote(reverse("pages-root"))
        if prefix:
            request.path = request.path.split("/")
            del request.path[pages_root.count('/')]
            request.path = "/".join(request.path)
            request.path_info = "/" + "/".join(request.path_info.split("/")[2:])
            t = prefix
            if t in SUPPORTED:
                lang = t
                if hasattr(request, "session"):
                    request.session["django_language"] = lang
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
        request.LANGUAGE_CODE = language
       
    def process_response(self, request, response):
        local_middleware = LocaleMiddleware()
        response =local_middleware.process_response(request, response)
        path = unicode(request.path)

        # note: pages_root is assumed to end in '/'.
        #       testing this and throwing an exception otherwise, would probably be a good idea
        pages_root = urllib.unquote(reverse("pages-root"))

        if not path.startswith(settings.MEDIA_URL) and \
                not path.startswith(settings.ADMIN_MEDIA_PREFIX) and \
                response.status_code == 200 and \
                response._headers['content-type'][1].split(';')[0] == "text/html":
            try:
                decoded_response = response.content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_response = response.content

            # Customarily user pages are served from http://the.server.com/~username/
            # When a user uses django-cms for his pages, the '~' of the url appears quoted in href links.
            # We have to quote pages_root for the regular expression to match.
            #
            # The used regex is quite complex. The exact pattern depends on the used settings.
            # The regex extracts the path of the url without the leading page root, but only matches urls
            # that don't already contain a language string or aren't considered multilingual.
            #
            # Here is an annotated example pattern (_r_ is a shorthand for the value of pages_root):
            #   pattern:        <a([^>]+)href="(?=_r_)(?!(/fr/|/de/|/en/|/pt-br/|/media/|/media/admin/))(_r_([^"]*))"([^>]*)>
            #                     |-\1--|                |---------------------\2---------------------| |   |-\4--|| |-\5--|
            #                                                                                           |----\3----|
            #   input (_r_=/):  <a href="/admin/password_change/" class="foo">
            #   matched groups: (u' ', None, u'/admin/password_change/', u'admin/password_change/', u' class="foo"')
            #
            # Notice that (?=...) and (?!=...) do not consume input or produce a group in the match object.
            # If the regex matches, the extracted path we want is stored in the fourth group (\4).
            HREF_URL_FIX_RE = re.compile(ur'<a([^>]+)href="(?=%s)(?!(%s|%s|%s))(%s([^"]*))"([^>]*)>' % (
                urllib.quote(pages_root),
                "|".join(map(lambda l: urllib.quote(pages_root) + l[0] + "/" , settings.CMS_LANGUAGES)),
                settings.MEDIA_URL,
                settings.ADMIN_MEDIA_PREFIX,
                urllib.quote(pages_root)
            ))

            # Unlike in href links, the '~' (see above) the '~' in form actions appears unquoted.
            #
            # For understanding this regex, please read the documentation for HREF_URL_FIX_RE above.
            FORM_URL_FIX_RE = re.compile(ur'<form([^>]+)action="(?=%s)(?!(%s|%s|%s))(%s([^"]*))"([^>]*)>' % (
                pages_root,
                "|".join(map(lambda l: pages_root + l[0] + "/" , settings.CMS_LANGUAGES)),
                settings.MEDIA_URL,
                settings.ADMIN_MEDIA_PREFIX,
                pages_root
            ))

            # Documentation comments for HREF_URL_FIX_RE above explain each match group (\1, \4, \5) represents.
            decoded_response = HREF_URL_FIX_RE.sub(ur'<a\1href="%s%s/\4"\5>' % (pages_root, request.LANGUAGE_CODE), decoded_response)
            response.content = FORM_URL_FIX_RE.sub(ur'<form\1action="%s%s/\4"\5>' % (pages_root, request.LANGUAGE_CODE), decoded_response).encode("utf8")

        if (response.status_code == 301 or response.status_code == 302 ):
            location = response['Location']
            if not has_lang_prefix(location) and location.startswith("/") and \
                    not location.startswith(settings.MEDIA_URL) and \
                    not location.startswith(settings.ADMIN_MEDIA_PREFIX):
                response['Location'] = "%s%s%s" % (pages_root, request.LANGUAGE_CODE, location[len(pages_root)-1:])
        response.set_cookie("django_language", request.LANGUAGE_CODE)
        return response
