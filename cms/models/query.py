"""Moved to :mod:`cms.pages.models.query`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "Case": "cms.pages.models.query.Case",
        "Counter": "cms.pages.models.query.Counter",
        "F": "cms.pages.models.query.F",
        "NoHomeFound": "cms.pages.models.query.NoHomeFound",
        "PageQuerySet": "cms.pages.models.query.PageQuerySet",
        "When": "cms.pages.models.query.When",
        "get_queryset_base": "cms.pages.models.query.get_queryset_base",
        "get_tree_backend": "cms.pages.models.query.get_tree_backend",
        "models": "cms.pages.models.query.models",
        "warnings": "cms.pages.models.query.warnings",
    },
    since="6.0",
    fallback="cms.pages.models.query",
)
