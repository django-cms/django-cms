# -*- coding: utf-8 -*-
import re
from cms.utils.conf import get_cms_setting

CMS_PAGE_CACHE_VERSION_KEY = get_cms_setting("CACHE_PREFIX") + '_PAGE_CACHE_VERSION'


def _get_cache_version():
    """
    Returns the current page cache version, explicitly setting one if not
    defined.
    """
    from django.core.cache import cache

    version = cache.get(CMS_PAGE_CACHE_VERSION_KEY)

    if version:
        return version
    else:
        _set_cache_version(1)
        return 1


def _set_cache_version(version):
    """
    Set the cache version to the specified value.
    """
    from django.core.cache import cache

    cache.set(
        CMS_PAGE_CACHE_VERSION_KEY,
        version,
        get_cms_setting('CACHE_DURATIONS')['content']
    )


def invalidate_cms_page_cache():
    """
    Invalidates the CMS PAGE CACHE.
    """

    #
    # NOTE: We're using a cache versioning strategy for invalidating the page
    # cache when necessary. Instead of wiping all the old entries, we simply
    # increment the version number rendering all previous entries
    # inaccessible and left to expire naturally.
    #
    # ALSO NOTE: According to the Django documentation, a timeout value of
    # `None' (in version 1.6+) is supposed to mean "cache forever", however,
    # this is actually only implemented as only slightly less than 30 days in
    # some backends (memcached, in particular). In older Djangos, `None' means
    # "use default value".  To avoid issues arising from different Django
    # versions and cache backend implementations, we will explicitly set the
    # lifespan of the CMS_PAGE_CACHE_VERSION entry to whatever is set in
    # settings.CACHE_DURATIONS['content']. This allows users to adjust as
    # necessary for their backend.
    #
    # To prevent writing cache entries that will live longer than our version
    # key, we will always re-write the current version number into the cache
    # just after we write any new cache entries, thus ensuring that the
    # version number will always outlive any entries written against that
    # version. This is a cheap operation.
    #
    # If there are no new cache writes before the version key expires, its
    # perfectly OK, since any previous entries cached against that version
    # will have also expired, so, it'd be pointless to try to access them
    # anyway.
    #
    version = _get_cache_version()
    _set_cache_version(version + 1)


CLEAN_KEY_PATTERN = re.compile(r'[^a-zA-Z0-9_-]')


def _clean_key(key):
    return CLEAN_KEY_PATTERN.sub('-', key)


def _get_cache_key(name, page_lookup, lang, site_id):
    from cms.models import Page
    if isinstance(page_lookup, Page):
        page_key = str(page_lookup.pk)
    else:
        page_key = str(page_lookup)
    page_key = _clean_key(page_key)
    return get_cms_setting('CACHE_PREFIX') + name + '__page_lookup:' + page_key + '_site:' + str(site_id) + '_lang:' + str(lang)
