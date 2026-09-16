"""Moved to :mod:`cms.pages.cache`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "Any": "cms.pages.cache.Any",
        "EXPIRE_NOW": "cms.pages.cache.EXPIRE_NOW",
        "MAX_EXPIRATION_TTL": "cms.pages.cache.MAX_EXPIRATION_TTL",
        "Mapping": "cms.pages.cache.Mapping",
        "TYPE_CHECKING": "cms.pages.cache.TYPE_CHECKING",
        "add_never_cache_headers": "cms.pages.cache.add_never_cache_headers",
        "annotations": "cms.pages.cache.annotations",
        "datetime": "cms.pages.cache.datetime",
        "get_cms_setting": "cms.pages.cache.get_cms_setting",
        "get_current_site": "cms.pages.cache.get_current_site",
        "get_default_language_for_site": "cms.pages.cache.get_default_language_for_site",
        "get_page_cache": "cms.pages.cache.get_page_cache",
        "get_page_url_cache": "cms.pages.cache.get_page_url_cache",
        "get_response_headers": "cms.pages.cache.get_response_headers",
        "get_timezone_name": "cms.pages.cache.get_timezone_name",
        "get_toolbar_from_request": "cms.pages.cache.get_toolbar_from_request",
        "get_xframe_cache": "cms.pages.cache.get_xframe_cache",
        "hashlib": "cms.pages.cache.hashlib",
        "iri_to_uri": "cms.pages.cache.iri_to_uri",
        "now": "cms.pages.cache.now",
        "patch_response_headers": "cms.pages.cache.patch_response_headers",
        "patch_vary_headers": "cms.pages.cache.patch_vary_headers",
        "set_page_cache": "cms.pages.cache.set_page_cache",
        "set_page_url_cache": "cms.pages.cache.set_page_url_cache",
        "set_xframe_cache": "cms.pages.cache.set_xframe_cache",
        "settings": "cms.pages.cache.settings",
        "timedelta": "cms.pages.cache.timedelta",
    },
    since="6.0",
    fallback="cms.pages.cache",
)
