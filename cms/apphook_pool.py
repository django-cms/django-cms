"""Moved to :mod:`cms.pages.apphook_pool`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "AppAlreadyRegistered": "cms.pages.apphook_pool.AppAlreadyRegistered",
        "ApphookPool": "cms.pages.apphook_pool.ApphookPool",
        "CMSApp": "cms.pages.apphook_pool.CMSApp",
        "ImproperlyConfigured": "cms.pages.apphook_pool.ImproperlyConfigured",
        "apphook_pool": "cms.pages.apphook_pool.apphook_pool",
        "autodiscover_modules": "cms.pages.apphook_pool.autodiscover_modules",
        "get_cms_setting": "cms.pages.apphook_pool.get_cms_setting",
        "import_string": "cms.pages.apphook_pool.import_string",
        "warnings": "cms.pages.apphook_pool.warnings",
    },
    since="6.0",
    fallback="cms.pages.apphook_pool",
)
