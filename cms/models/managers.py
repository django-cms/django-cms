"""Moved: the managers now live with the models they serve.

=============================== =========================================
``PageManager``, ``PageUrlManager``, ``PageContentManager``,
``ContentAdminQuerySet``, ``ContentAdminManager``, ``WithUserMixin``
                                :mod:`cms.pages.models.managers`
``PlaceholderManager``, ``PlaceholderForObjQS``
                                :mod:`cms.core.models.managers`
``BasicPagePermissionManager``, ``GlobalPagePermissionManager``,
``PagePermissionManager``       :mod:`cms.permissions.managers`
=============================== =========================================

Kept importable because the ecosystem imports from this path (see
:mod:`cms.compat`). This module was split rather than moved, so there is no
single fallback target.
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "ContentAdminManager": "cms.pages.models.managers.ContentAdminManager",
        "ContentAdminQuerySet": "cms.pages.models.managers.ContentAdminQuerySet",
        "PageContentManager": "cms.pages.models.managers.PageContentManager",
        "PageManager": "cms.pages.models.managers.PageManager",
        "PageUrlManager": "cms.pages.models.managers.PageUrlManager",
        "WithUserMixin": "cms.pages.models.managers.WithUserMixin",
        "PlaceholderForObjQS": "cms.core.models.managers.PlaceholderForObjQS",
        "PlaceholderManager": "cms.core.models.managers.PlaceholderManager",
        "BasicPagePermissionManager": "cms.permissions.managers.BasicPagePermissionManager",
        "GlobalPagePermissionManager": "cms.permissions.managers.GlobalPagePermissionManager",
        "PagePermissionManager": "cms.permissions.managers.PagePermissionManager",
    },
    since="6.0",
)
