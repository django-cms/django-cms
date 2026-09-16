"""Moved to :mod:`cms.core.cache`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "clear_placeholder_cache": "cms.core.cache.clear_placeholder_cache",
        "get_cms_setting": "cms.core.cache.get_cms_setting",
        "get_header_name": "cms.core.cache.get_header_name",
        "get_placeholder_cache": "cms.core.cache.get_placeholder_cache",
        "get_timezone_name": "cms.core.cache.get_timezone_name",
        "hashlib": "cms.core.cache.hashlib",
        "now": "cms.core.cache.now",
        "set_placeholder_cache": "cms.core.cache.set_placeholder_cache",
        "time": "cms.core.cache.time",
    },
    since="6.0",
    fallback="cms.core.cache",
)
