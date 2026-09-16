"""Moved to :mod:`cms.permissions.models`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "ACCESS_CHILDREN": "cms.permissions.models.ACCESS_CHILDREN",
        "ACCESS_CHOICES": "cms.permissions.models.ACCESS_CHOICES",
        "ACCESS_DESCENDANTS": "cms.permissions.models.ACCESS_DESCENDANTS",
        "ACCESS_PAGE": "cms.permissions.models.ACCESS_PAGE",
        "ACCESS_PAGE_AND_CHILDREN": "cms.permissions.models.ACCESS_PAGE_AND_CHILDREN",
        "ACCESS_PAGE_AND_DESCENDANTS": "cms.permissions.models.ACCESS_PAGE_AND_DESCENDANTS",
        "AbstractPagePermission": "cms.permissions.models.AbstractPagePermission",
        "EDIT_PERMISSION_REQUIRED_MESSAGES": "cms.permissions.models.EDIT_PERMISSION_REQUIRED_MESSAGES",
        "GlobalPagePermission": "cms.permissions.models.GlobalPagePermission",
        "GlobalPagePermissionManager": "cms.permissions.models.GlobalPagePermissionManager",
        "Group": "cms.permissions.models.Group",
        "ImproperlyConfigured": "cms.permissions.models.ImproperlyConfigured",
        "MASK_CHILDREN": "cms.permissions.models.MASK_CHILDREN",
        "MASK_DESCENDANTS": "cms.permissions.models.MASK_DESCENDANTS",
        "MASK_PAGE": "cms.permissions.models.MASK_PAGE",
        "Page": "cms.permissions.models.Page",
        "PagePermission": "cms.permissions.models.PagePermission",
        "PagePermissionManager": "cms.permissions.models.PagePermissionManager",
        "PageUser": "cms.permissions.models.PageUser",
        "PageUserGroup": "cms.permissions.models.PageUserGroup",
        "PageUserManager": "cms.permissions.models.PageUserManager",
        "PermissionTuple": "cms.permissions.models.PermissionTuple",
        "Q": "cms.permissions.models.Q",
        "Site": "cms.permissions.models.Site",
        "User": "cms.permissions.models.User",
        "UserManager": "cms.permissions.models.UserManager",
        "ValidationError": "cms.permissions.models.ValidationError",
        "apps": "cms.permissions.models.apps",
        "force_str": "cms.permissions.models.force_str",
        "models": "cms.permissions.models.models",
        "settings": "cms.permissions.models.settings",
    },
    since="6.0",
    fallback="cms.permissions.models",
)
