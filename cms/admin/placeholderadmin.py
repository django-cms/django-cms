"""Moved to :mod:`cms.core.admin.placeholder`.

Kept importable because third-party packages subclass these by this path
(see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "BaseEditableAdminMixin": "cms.core.admin.placeholder.BaseEditableAdminMixin",
        "FrontendEditableAdminMixin": "cms.core.admin.placeholder.FrontendEditableAdminMixin",
        "PlaceholderAdmin": "cms.core.admin.placeholder.PlaceholderAdmin",
        "get_int": "cms.core.admin.placeholder.get_int",
    },
    since="6.0",
    fallback="cms.core.admin.placeholder",
)
