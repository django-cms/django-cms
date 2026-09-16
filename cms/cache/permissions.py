"""Moved to :mod:`cms.permissions.cache`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "PERMISSION_KEYS": "cms.permissions.cache.PERMISSION_KEYS",
        "clear_permission_cache": "cms.permissions.cache.clear_permission_cache",
        "clear_user_permission_cache": "cms.permissions.cache.clear_user_permission_cache",
        "get_cache_key": "cms.permissions.cache.get_cache_key",
        "get_cache_permission_version": "cms.permissions.cache.get_cache_permission_version",
        "get_cache_permission_version_key": "cms.permissions.cache.get_cache_permission_version_key",
        "get_cms_setting": "cms.permissions.cache.get_cms_setting",
        "get_permission_cache": "cms.permissions.cache.get_permission_cache",
        "set_permission_cache": "cms.permissions.cache.set_permission_cache",
    },
    since="6.0",
    fallback="cms.permissions.cache",
)
