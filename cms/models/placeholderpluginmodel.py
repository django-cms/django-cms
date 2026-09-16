"""Moved to :mod:`cms.core.models.placeholderplugin`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "CMSPlugin": "cms.core.models.placeholderplugin.CMSPlugin",
        "PlaceholderReference": "cms.core.models.placeholderplugin.PlaceholderReference",
        "PlaceholderRelationField": "cms.core.models.placeholderplugin.PlaceholderRelationField",
        "cached_property": "cms.core.models.placeholderplugin.cached_property",
        "get_placeholder_from_slot": "cms.core.models.placeholderplugin.get_placeholder_from_slot",
        "models": "cms.core.models.placeholderplugin.models",
    },
    since="6.0",
    fallback="cms.core.models.placeholderplugin",
)
