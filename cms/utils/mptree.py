"""Moved to :mod:`cms.pages.mptree`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "Concat": "cms.pages.mptree.Concat",
        "DEFAULT_ALPHABET": "cms.pages.mptree.DEFAULT_ALPHABET",
        "DEFAULT_STEPLEN": "cms.pages.mptree.DEFAULT_STEPLEN",
        "F": "cms.pages.mptree.F",
        "Length": "cms.pages.mptree.Length",
        "MaterializedPath": "cms.pages.mptree.MaterializedPath",
        "MaterializedPathMixin": "cms.pages.mptree.MaterializedPathMixin",
        "Substr": "cms.pages.mptree.Substr",
        "TREE_FIELDS": "cms.pages.mptree.TREE_FIELDS",
        "TreePathOverflow": "cms.pages.mptree.TreePathOverflow",
        "Value": "cms.pages.mptree.Value",
        "defaultdict": "cms.pages.mptree.defaultdict",
        "get_queryset_base": "cms.pages.mptree.get_queryset_base",
        "get_tree_backend": "cms.pages.mptree.get_tree_backend",
        "get_tree_base": "cms.pages.mptree.get_tree_base",
        "models": "cms.pages.mptree.models",
        "router": "cms.pages.mptree.router",
        "transaction": "cms.pages.mptree.transaction",
        "wraps": "cms.pages.mptree.wraps",
    },
    since="6.0",
    fallback="cms.pages.mptree",
)
