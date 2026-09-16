"""Moved to :mod:`cms.permissions.signals`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "PageUser": "cms.permissions.signals.PageUser",
        "PageUserGroup": "cms.permissions.signals.PageUserGroup",
        "User": "cms.permissions.signals.User",
        "clear_user_permission_cache": "cms.permissions.signals.clear_user_permission_cache",
        "get_user_model": "cms.permissions.signals.get_user_model",
        "menu_pool": "cms.permissions.signals.menu_pool",
        "post_save_user": "cms.permissions.signals.post_save_user",
        "post_save_user_group": "cms.permissions.signals.post_save_user_group",
        "pre_delete_globalpagepermission": "cms.permissions.signals.pre_delete_globalpagepermission",
        "pre_delete_group": "cms.permissions.signals.pre_delete_group",
        "pre_delete_pagepermission": "cms.permissions.signals.pre_delete_pagepermission",
        "pre_delete_user": "cms.permissions.signals.pre_delete_user",
        "pre_save_globalpagepermission": "cms.permissions.signals.pre_save_globalpagepermission",
        "pre_save_group": "cms.permissions.signals.pre_save_group",
        "pre_save_pagepermission": "cms.permissions.signals.pre_save_pagepermission",
        "pre_save_user": "cms.permissions.signals.pre_save_user",
        "user_m2m_changed": "cms.permissions.signals.user_m2m_changed",
    },
    since="6.0",
    fallback="cms.permissions.signals",
)
