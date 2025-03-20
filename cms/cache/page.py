import hashlib
from datetime import timedelta

from django.conf import settings
from django.utils.cache import (
    add_never_cache_headers,
    patch_response_headers,
    patch_vary_headers,
)
from django.utils.encoding import iri_to_uri
from django.utils.timezone import now

from cms.cache import _get_cache_key, _get_cache_version, _set_cache_version
from cms.constants import EXPIRE_NOW, MAX_EXPIRATION_TTL
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.compat.response import get_response_headers
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import get_timezone_name
from cms.utils.i18n import get_default_language_for_site


def _page_cache_key(request):
    """
    Generate a cache key based on the request path and language.
    The language is determined following django-cms's language resolution order.
    """
    if hasattr(request, "LANGUAGE_CODE"):
        language = request.LANGUAGE_CODE
    else:
        language = get_default_language_for_site(settings.SITE_ID)

    cache_key = "%s:%d:%s:%s" % (
        get_cms_setting("CACHE_PREFIX"),
        settings.SITE_ID,
        language,
        hashlib.sha1(iri_to_uri(request.get_full_path()).encode("utf-8")).hexdigest(),
    )
    if settings.USE_TZ:
        cache_key += ".%s" % get_timezone_name()
    return cache_key


def set_page_cache(response):
    from django.core.cache import cache

    request = response._request
    toolbar = get_toolbar_from_request(request)
    is_authenticated = request.user.is_authenticated

    if is_authenticated or toolbar._cache_disabled or not get_cms_setting("PAGE_CACHE"):
        add_never_cache_headers(response)
        return response

    # This *must* be TZ-aware
    timestamp = now()

    placeholders = toolbar.content_renderer.get_rendered_placeholders()
    # Checks if there's a plugin using the legacy "cache = False"
    placeholder_ttl_list = []
    vary_cache_on_set = set()
    for ph in placeholders:
        # get_cache_expiration() always returns:
        #     EXPIRE_NOW <= int <= MAX_EXPIRATION_IN_SECONDS
        ttl = ph.get_cache_expiration(request, timestamp)
        vary_cache_on = ph.get_vary_cache_on(request)

        placeholder_ttl_list.append(ttl)
        if ttl and vary_cache_on:
            # We're only interested in vary headers if they come from
            # a cache-able placeholder.
            vary_cache_on_set |= set(vary_cache_on)

    if EXPIRE_NOW not in placeholder_ttl_list:
        if placeholder_ttl_list:
            min_placeholder_ttl = min(x for x in placeholder_ttl_list)
        else:
            # Should only happen when there are no placeholders at all
            min_placeholder_ttl = MAX_EXPIRATION_TTL
        ttl = min(get_cms_setting("CACHE_DURATIONS")["content"], min_placeholder_ttl)

        if ttl > 0:
            # Adds expiration, etc. to headers
            patch_response_headers(response, cache_timeout=ttl)
            patch_vary_headers(response, sorted(vary_cache_on_set))

            version = _get_cache_version()
            # We also store the absolute expiration timestamp to avoid
            # recomputing it on cache-reads.
            expires_datetime = timestamp + timedelta(seconds=ttl)
            response_headers = get_response_headers(response)
            cache.set(
                _page_cache_key(request),
                (
                    response.content,
                    response_headers,
                    expires_datetime,
                ),
                ttl,
                version=version,
            )
            # See note in invalidate_cms_page_cache()
            _set_cache_version(version)
    return response


def get_page_cache(request):
    from django.core.cache import cache

    return cache.get(_page_cache_key(request), version=_get_cache_version())


def get_xframe_cache(page):
    from django.core.cache import cache

    return cache.get("cms:xframe_options:%s" % page.pk)


def set_xframe_cache(page, xframe_options):
    from django.core.cache import cache

    cache.set("cms:xframe_options:%s" % page.pk, xframe_options, version=_get_cache_version())
    _set_cache_version(_get_cache_version())


def _page_url_key(page_lookup, lang, site_id):
    return _get_cache_key("page_url", page_lookup, lang, site_id) + "_type:absolute_url"


def set_page_url_cache(page_lookup, lang, site_id, url):
    from django.core.cache import cache

    cache.set(
        _page_url_key(page_lookup, lang, site_id),
        url,
        get_cms_setting("CACHE_DURATIONS")["content"],
        version=_get_cache_version(),
    )
    _set_cache_version(_get_cache_version())


def get_page_url_cache(page_lookup, lang, site_id):
    from django.core.cache import cache

    return cache.get(_page_url_key(page_lookup, lang, site_id), version=_get_cache_version())
