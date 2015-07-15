# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.timezone import get_current_timezone_name
from cms.cache import _get_cache_version, _set_cache_version, _clean_key, _get_cache_key
from cms.utils import get_cms_setting


def _placeholder_cache_key(placeholder, lang):
    cache_key = '%srender_placeholder:%s.%s' % (get_cms_setting("CACHE_PREFIX"), placeholder.pk, str(lang))
    if settings.USE_TZ:
        tz_name = force_text(get_current_timezone_name(), errors='ignore')
        cache_key += '.%s' % tz_name.encode('ascii', 'ignore').decode('ascii').replace(' ', '_')
    return cache_key


def set_placeholder_cache(placeholder, lang, content):
    """
    Caches the rendering of a placeholder
    """
    from django.core.cache import cache
    cache.set(_placeholder_cache_key(placeholder, lang),
              content,
              get_cms_setting('CACHE_DURATIONS')['content'],
              version=_get_cache_version())
    _set_cache_version(_get_cache_version())


def get_placeholder_cache(placeholder, lang):
    """
    Retrieves the cached content of a placeholder
    """
    from django.core.cache import cache

    return cache.get(_placeholder_cache_key(placeholder, lang),
                     version=_get_cache_version())


def clear_placeholder_cache(placeholder, lang):
    from django.core.cache import cache

    cache.delete(_placeholder_cache_key(placeholder, lang), version=_get_cache_version())


def _placeholder_page_cache_key(page_lookup, lang, site_id, placeholder_name):
    base_key = _get_cache_key('_show_placeholder_for_page', page_lookup, lang, site_id)
    return _clean_key('%s_placeholder:%s' % (base_key, placeholder_name))


def get_placeholder_page_cache(page_lookup, lang, site_id, placeholder_name):
    from django.core.cache import cache

    return cache.get(_placeholder_page_cache_key(page_lookup, lang, site_id, placeholder_name),
                     version=_get_cache_version())


def set_placeholder_page_cache(page_lookup, lang, site_id, placeholder_name, content):
    from django.core.cache import cache

    cache.set(_placeholder_page_cache_key(page_lookup, lang, site_id, placeholder_name),
              content,
              get_cms_setting('CACHE_DURATIONS')['content'], version=_get_cache_version())
    _set_cache_version(_get_cache_version())
