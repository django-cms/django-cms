"""Moved to :mod:`cms.pages.models.apphooks_reload`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "UrlconfRevision": "cms.pages.models.apphooks_reload.UrlconfRevision",
        "models": "cms.pages.models.apphooks_reload.models",
        "uuid": "cms.pages.models.apphooks_reload.uuid",
    },
    since="6.0",
    fallback="cms.pages.models.apphooks_reload",
)
