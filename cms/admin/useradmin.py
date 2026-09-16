"""Moved to :mod:`cms.permissions.useradmin`.

Kept importable because third-party packages subclass these by this path
(see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "GenericCmsPermissionAdmin": "cms.permissions.useradmin.GenericCmsPermissionAdmin",
        "PageUserAdmin": "cms.permissions.useradmin.PageUserAdmin",
        "PageUserGroupAdmin": "cms.permissions.useradmin.PageUserGroupAdmin",
    },
    since="6.0",
    fallback="cms.permissions.useradmin",
)
