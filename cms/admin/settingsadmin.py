"""Moved to :mod:`cms.core.admin.settings`.

Kept importable because third-party packages subclass these by this path
(see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "SettingsAdmin": "cms.core.admin.settings.SettingsAdmin",
    },
    since="6.0",
    fallback="cms.core.admin.settings",
)
