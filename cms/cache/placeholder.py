# -*- coding: utf-8 -*-

"""
This module manages placeholder caching. We use a cache-versioning strategy
with each (placeholder x lang) manages its own version. The actual cache
includes additional keys appropriate for the placeholders get_vary_cache_on().

Invalidation of a placeholder's cache simply increments the version number for
the (placeholder x lang) pair, which renders any cache entries for that
placeholder under that version inaccessible. Those cache entries will simply
expire and will be purged according to the policy of the cache backend in-use.

The cache entries themselves may include additional sub-keys, according to the
list of VARY header-names as returned by placeholder.get_vary_cache_on() and
the current HTTPRequest object.

The vary-on header-names are also stored with the version. This enables us to
check for cache hits without re-computing placeholder.get_vary_cache_on().
"""

import hashlib
import time

from django.utils.timezone import now

from cms.utils import get_cms_setting
from cms.utils.helpers import get_header_name, get_timezone_name


def _get_placeholder_cache_version_key(placeholder, lang):
    """
    Returns the version key for the given «placeholder» and «lang».

    Invalidating this (via clear_placeholder_cache by replacing the stored
    value with a new value) will effectively make all "sub-caches" relating to
    this (placeholder x lang) inaccessible. Sub-caches include caches per TZ
    and per VARY header.
    """
    # TODO: Should we also add the site ID to the key?
    prefix = get_cms_setting('CACHE_PREFIX')
    key = '{prefix}|placeholder_cache_version|id:{id}|lang:{lang}'.format(
        prefix=prefix,
        id=placeholder.pk,
        lang=str(lang)
    )
    if len(key) > 250:
        key = '{prefix}|{hash}'.format(
            prefix=prefix,
            hash=hashlib.md5(key.encode('utf-8')).hexdigest(),
        )
    return key


def _get_placeholder_cache_version(placeholder, lang):
    """
    Gets the (placeholder x lang)'s current version and vary-on header-names
    list, if present, otherwise resets to («timestamp», []).
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_version_key(placeholder, lang)
    cached = cache.get(key)
    if cached:
        version, vary_on_list = cached
    else:
        version = int(time.time() * 1000000)
        vary_on_list = list()
        _set_placeholder_cache_version(placeholder, lang, version, vary_on_list)
    return version, vary_on_list


def _set_placeholder_cache_version(placeholder, lang, version, vary_on_list=None, duration=None):
    """
    Sets the (placeholder x lang)'s version and vary-on header-names list.
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_version_key(placeholder, lang)

    if not duration or version < 1:
        cache.delete(key)

    if vary_on_list is None:
        vary_on_list = list()

    cache.set(key, (version, vary_on_list), duration)


def _get_placeholder_cache_key(placeholder, lang, request, soft=False):
    """
    Returns the fully-addressed cache key for the given placeholder and
    the request.

    The kwarg «soft» should be set to True if getting the cache key to then
    read from the cache. If instead the key retrieval is to support a cache
    write, let «soft» be False.
    """
    # TODO: Should we also add the site ID to the key?
    prefix = get_cms_setting('CACHE_PREFIX')
    version, vary_on_list = _get_placeholder_cache_version(placeholder, lang)
    main_key = '{prefix}|render_placeholder|id:{id}|lang:{lang}|tz:{tz}|v:{version}'.format(
        prefix=prefix,
        id=placeholder.pk,
        lang=lang,
        tz=get_timezone_name(),
        version=version,
    )

    if not soft:
        # We are about to write to the cache, so we want to get the latest
        # vary_cache_on headers and the correct cache expiration, ignoring any
        # we already have. If the placeholder has already been rendered, this
        # will be very efficient (zero-additional queries) due to the caching
        # of all its plugins during the rendering process anyway.
        vary_on_list = placeholder.get_vary_cache_on(request)
        duration = placeholder.get_cache_expiration(request, now())
        # Update the main placeholder cache version
        _set_placeholder_cache_version(
            placeholder, lang, version, vary_on_list, duration)

    sub_key_list = []
    for key in vary_on_list:
        value = request.META.get(get_header_name(key)) or '_'
        sub_key_list.append(key + ':' + value)

    cache_key = main_key
    if sub_key_list:
        cache_key += '|' + '|'.join(sub_key_list)

    if len(cache_key) > 250:
        cache_key = '{prefix}|{hash}'.format(
            prefix=prefix,
            hash=hashlib.md5(cache_key.encode('utf-8')).hexdigest(),
        )

    return cache_key


def set_placeholder_cache(placeholder, lang, content, request):
    """
    Sets the (correct) placeholder cache with the rendered placeholder.
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_key(placeholder, lang, request)

    duration = min(
      get_cms_setting('CACHE_DURATIONS')['content'],
      placeholder.get_cache_expiration(request, now())
    )
    cache.set(key, content, duration)

    # "touch" the cache-version, so that it stays as fresh as this content.
    version, vary_on_list = _get_placeholder_cache_version(placeholder, lang)
    _set_placeholder_cache_version(
        placeholder, lang, version, vary_on_list, duration=duration)


def get_placeholder_cache(placeholder, lang, request):
    """
    Returns the placeholder from cache respecting the placeholder's
    VARY headers.
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_key(placeholder, lang, request, soft=True)
    content = cache.get(key)
    return content


def clear_placeholder_cache(placeholder, lang):
    """
    Invalidates all existing cache entries for this (placeholder x lang) pair.
    We don't need to re-store the vary_on_list, because the cache is now
    effectively empty.
    """
    current_version, _ = _get_placeholder_cache_version(placeholder, lang)
    version = int(time.time() * 1000000)
    if current_version >= version:
        version = current_version + 1
    _set_placeholder_cache_version(placeholder, lang, version, list())


# The following code supports only the show_placeholder template tag
from cms.cache import _get_cache_version, _set_cache_version, _clean_key, _get_cache_key


def _placeholder_page_cache_key(page_lookup, lang, site_id, placeholder_name):
    base_key = _get_cache_key('_show_placeholder_for_page', page_lookup, lang, site_id)
    return _clean_key('%s_placeholder:%s' % (base_key, placeholder_name))


def get_placeholder_page_cache(page_lookup, lang, site_id, placeholder_name):
    from django.core.cache import cache

    return cache.get(
        _placeholder_page_cache_key(page_lookup, lang, site_id, placeholder_name),
        version=_get_cache_version()
    )


def set_placeholder_page_cache(page_lookup, lang, site_id, placeholder_name, content):
    from django.core.cache import cache

    cache.set(
        _placeholder_page_cache_key(page_lookup, lang, site_id, placeholder_name),
        content,
        get_cms_setting('CACHE_DURATIONS')['content'],
        version=_get_cache_version()
    )
    _set_cache_version(_get_cache_version())
