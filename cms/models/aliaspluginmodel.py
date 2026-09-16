"""Moved to :mod:`cms.core.models.aliasplugin`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "AliasPluginModel": "cms.core.models.aliasplugin.AliasPluginModel",
        "CMSPlugin": "cms.core.models.aliasplugin.CMSPlugin",
        "Placeholder": "cms.core.models.aliasplugin.Placeholder",
        "Q": "cms.core.models.aliasplugin.Q",
        "force_str": "cms.core.models.aliasplugin.force_str",
        "models": "cms.core.models.aliasplugin.models",
    },
    since="6.0",
    fallback="cms.core.models.aliasplugin",
)
