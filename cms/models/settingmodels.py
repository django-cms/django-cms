"""Moved to :mod:`cms.core.models.settings`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "PlaceholderForeignKey": "cms.core.models.settings.PlaceholderForeignKey",
        "UserSettings": "cms.core.models.settings.UserSettings",
        "force_str": "cms.core.models.settings.force_str",
        "models": "cms.core.models.settings.models",
        "settings": "cms.core.models.settings.settings",
    },
    since="6.0",
    fallback="cms.core.models.settings",
)
