"""Moved to :mod:`cms.permissions.admin`.

Kept importable because third-party packages subclass these by this path
(see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "GlobalPagePermissionAdmin": "cms.permissions.admin.GlobalPagePermissionAdmin",
        "PERMISSION_ADMIN_INLINES": "cms.permissions.admin.PERMISSION_ADMIN_INLINES",
        "PagePermissionInlineAdmin": "cms.permissions.admin.PagePermissionInlineAdmin",
        "TabularInline": "cms.permissions.admin.TabularInline",
        "ViewRestrictionInlineAdmin": "cms.permissions.admin.ViewRestrictionInlineAdmin",
    },
    since="6.0",
    fallback="cms.permissions.admin",
)
