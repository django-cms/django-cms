# -*- coding: utf-8 -*-
import hashlib
from django.conf import settings
from django.utils.cache import add_never_cache_headers
from django.utils.encoding import iri_to_uri, force_text
from django.utils.timezone import get_current_timezone_name

from cms.cache import _get_cache_version, _set_cache_version, _get_cache_key
from cms.utils import get_cms_setting


def _page_cache_key(request):
    #md5 key of current path
    cache_key = "%s:%d:%s" % (
        get_cms_setting("CACHE_PREFIX"),
        settings.SITE_ID,
        hashlib.md5(iri_to_uri(request.get_full_path()).encode('utf-8')).hexdigest()
    )
    if settings.USE_TZ:
        # The datetime module doesn't restrict the output of tzname().
        # Windows is known to use non-standard, locale-dependant names.
        # User-defined tzinfo classes may return absolutely anything.
        # Hence this paranoid conversion to create a valid cache key.
        tz_name = force_text(get_current_timezone_name(), errors='ignore')
        cache_key += '.%s' % tz_name.encode('ascii', 'ignore').decode('ascii').replace(' ', '_')
    return cache_key


def set_page_cache(response):
    from django.core.cache import cache

    if not get_cms_setting('PAGE_CACHE'):
        return response
    request = response._request
    save_cache = True
    for placeholder in getattr(request, 'placeholders', []):
        if not placeholder.cache_placeholder:
            save_cache = False
            break
    if hasattr(request, 'toolbar'):
        if request.toolbar.edit_mode or request.toolbar.show_toolbar:
            save_cache = False
    if request.user.is_authenticated():
        save_cache = False
    if not save_cache:
        add_never_cache_headers(response)
        return response
    else:
        version = _get_cache_version()
        ttl = get_cms_setting('CACHE_DURATIONS')['content']

        cache.set(
            _page_cache_key(request),
            (response.content, response._headers),
            ttl,
            version=version
        )
        # See note in invalidate_cms_page_cache()
        _set_cache_version(version)


def get_page_cache(request):
    from django.core.cache import cache

    return cache.get(_page_cache_key(request),
                     version=_get_cache_version())


def get_xframe_cache(page):
    from django.core.cache import cache
    return cache.get('cms:xframe_options:%s' % page.pk)


def set_xframe_cache(page, xframe_options):
    from django.core.cache import cache
    cache.set('cms:xframe_options:%s' % page.pk,
              xframe_options,
              version=_get_cache_version())
    _set_cache_version(_get_cache_version())


def _page_url_key(page_lookup, lang, site_id):
    return _get_cache_key('page_url', page_lookup, lang, site_id) + '_type:absolute_url'


def set_page_url_cache(page_lookup, lang, site_id, url):
    from django.core.cache import cache
    cache.set(_page_url_key(page_lookup, lang, site_id),
              url,
              get_cms_setting('CACHE_DURATIONS')['content'], version=_get_cache_version())
    _set_cache_version(_get_cache_version())


def get_page_url_cache(page_lookup, lang, site_id):
    from django.core.cache import cache
    return cache.get(_page_url_key(page_lookup, lang, site_id),
                     version=_get_cache_version())
