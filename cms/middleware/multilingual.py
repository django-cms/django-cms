# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.i18n import get_default_language
from django.conf import settings
from django.core.urlresolvers import reverse
from django.middleware.locale import LocaleMiddleware
from django.utils import translation
import re
import urllib
import urlparse

HAS_LANG_PREFIX_RE = re.compile(r"^/(%s)/.*" % "|".join([re.escape(lang[0]) for lang in settings.CMS_LANGUAGES]))


def has_lang_prefix(path):
    check = HAS_LANG_PREFIX_RE.match(path)
    if check is not None:
        return check.group(1)
    else:
        return False


def patch_response(content, pages_root, language):
    # Customarily user pages are served from http://the.server.com/~username/
    # When a user uses django-cms for his pages, the '~' of the url appears quoted in href links.
    # We have to quote pages_root for the regular expression to match.
    #
    # The used regex is quite complex. The exact pattern depends on the used settings.
    # The regex extracts the path of the url without the leading page root, but only matches urls
    # that don't already contain a language string or aren't considered multilingual.
    #
    # Here is an annotated example pattern (_r_ is a shorthand for the value of pages_root):
    #   pattern:        <a([^>]+)href=("|\')(?=_r_)(?!(/fr/|/de/|/en/|/pt-br/|/media/|/media/admin/))(_r_(.*?))("|\')(.*?)>
    #                     |-\1--|     |-\2-|       |---------------------\3---------------------|    | |-\5--|||-\6-||-\7-|
    #                                                                                                |---\4---|
    #   input (_r_=/):  <a href="/admin/password_change/" class="foo">
    #   matched groups: (u' ', None, u'/admin/password_change/', u'admin/password_change/', u' class="foo"')
    #
    # Notice that (?=...) and (?!=...) do not consume input or produce a group in the match object.
    # If the regex matches, the extracted path we want is stored in the fourth group (\4).
    quoted_root = urllib.quote(pages_root)
    ignore_paths = ['%s%s/' % (quoted_root, lang[0]) for lang in settings.CMS_LANGUAGES]
    ignore_paths += [settings.MEDIA_URL]
    if getattr(settings, 'ADMIN_MEDIA_PREFIX', False):
        ignore_paths += [settings.ADMIN_MEDIA_PREFIX]
    if getattr(settings,'STATIC_URL', False):
        ignore_paths += [settings.STATIC_URL]

    HREF_URL_FIX_RE = re.compile(ur'<a([^>]+)href=("|\')(?=%s)(?!(%s))(%s(.*?))("|\')(.*?)>' % (
        quoted_root,
        "|".join([re.escape(p) for p in ignore_paths]),
        quoted_root
    ))

    # Unlike in href links, the '~' (see above) the '~' in form actions appears unquoted.
    #
    # For understanding this regex, please read the documentation for HREF_URL_FIX_RE above.

    ignore_paths = ['%s%s/' % (pages_root, lang[0]) for lang in settings.CMS_LANGUAGES]
    ignore_paths += [settings.MEDIA_URL]
    if getattr(settings, 'ADMIN_MEDIA_PREFIX', False):
        ignore_paths += [settings.ADMIN_MEDIA_PREFIX]
    if getattr(settings,'STATIC_URL', False):
        ignore_paths += [settings.STATIC_URL]
    FORM_URL_FIX_RE = re.compile(ur'<form([^>]+)action=("|\')(?=%s)(?!(%s))(%s(.*?))("|\')(.*?)>' % (
        pages_root,
        "|".join([re.escape(p) for p in ignore_paths]),
        pages_root
    ))

    content = HREF_URL_FIX_RE.sub(ur'<a\1href=\2/%s%s\5\6\7>' % (language, pages_root), content)
    content = FORM_URL_FIX_RE.sub(ur'<form\1action=\2/%s%s\5\6\7>' % (language, pages_root), content).encode("utf8")
    return content


class MultilingualURLMiddleware(object):
    def get_language_from_request(self, request):
        prefix = has_lang_prefix(request.path_info)
        lang = None
        if prefix:
            request.path = "/" + "/".join(request.path.split("/")[2:])
            request.path_info = "/" + "/".join(request.path_info.split("/")[2:])
            t = prefix
            if t in settings.CMS_FRONTEND_LANGUAGES:
                lang = t
        if not lang:
            languages = []
            for frontend_lang in settings.CMS_FRONTEND_LANGUAGES:
                languages.append((frontend_lang,frontend_lang))
            with SettingsOverride(LANGUAGES=languages):
                lang = translation.get_language_from_request(request)
        if not lang:
            lang = get_default_language()
        old_lang = None
        if hasattr(request, "session") and request.session.get("django_language", None):
            old_lang = request.session["django_language"]
        if not old_lang and hasattr(request, "COOKIES") and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, None):
            old_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if old_lang != lang:
            if hasattr(request, 'session'):
                request.session['django_language'] = lang
        return lang

    def process_request(self, request):
        language = self.get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language

    def process_response(self, request, response):
        language = getattr(request, 'LANGUAGE_CODE', self.get_language_from_request(request))
        local_middleware = LocaleMiddleware()
        response = local_middleware.process_response(request, response)
        path = unicode(request.path)
        if not hasattr(request, 'session') and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != language:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
        # note: pages_root is assumed to end in '/'.
        #       testing this and throwing an exception otherwise, would probably be a good idea

        if (not path.startswith(settings.MEDIA_URL) and
                not path.startswith(settings.STATIC_URL) and
                not (getattr(settings, 'STATIC_URL', False) and path.startswith(settings.STATIC_URL)) and
                response.status_code == 200 and
                response.has_header('Content-Type') and
                response._headers['content-type'][1].split(';')[0] == "text/html"):
            pages_root = urllib.unquote(reverse("pages-root"))
            try:
                decoded_response = response.content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_response = response.content

            response.content = patch_response(
                decoded_response,
                pages_root,
                request.LANGUAGE_CODE
            )

        if response.status_code == 301 or response.status_code == 302:
            location = response['Location']
            if location.startswith('.'):
                location = urlparse.urljoin(request.path, location)
                response['Location'] = location
            if (not has_lang_prefix(location) and location.startswith("/") and
                    not location.startswith(settings.MEDIA_URL) and
                    not (getattr(settings, 'STATIC_URL', False) and location.startswith(settings.STATIC_URL))):
                response['Location'] = "/%s%s" % (language, location)
        if request.COOKIES.get('django_language') != language:
            response.set_cookie("django_language", language)
        return response
