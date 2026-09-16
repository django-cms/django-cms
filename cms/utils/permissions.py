"""Moved to :mod:`cms.permissions.utils`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "ContextVar": "cms.permissions.utils.ContextVar",
        "GlobalPagePermission": "cms.permissions.utils.GlobalPagePermission",
        "Group": "cms.permissions.utils.Group",
        "NoPermissionsException": "cms.permissions.utils.NoPermissionsException",
        "PagePermission": "cms.permissions.utils.PagePermission",
        "Q": "cms.permissions.utils.Q",
        "ROOT_USER_LEVEL": "cms.permissions.utils.ROOT_USER_LEVEL",
        "SCRIPT_USERNAME": "cms.permissions.utils.SCRIPT_USERNAME",
        "available_attrs": "cms.permissions.utils.available_attrs",
        "cached_func": "cms.permissions.utils.cached_func",
        "clear_func_cache": "cms.permissions.utils.clear_func_cache",
        "clear_permission_lru_caches": "cms.permissions.utils.clear_permission_lru_caches",
        "contextmanager": "cms.permissions.utils.contextmanager",
        "current_user": "cms.permissions.utils.current_user",
        "defaultdict": "cms.permissions.utils.defaultdict",
        "get_clean_username": "cms.permissions.utils.get_clean_username",
        "get_cms_setting": "cms.permissions.utils.get_cms_setting",
        "get_current_user": "cms.permissions.utils.get_current_user",
        "get_current_user_name": "cms.permissions.utils.get_current_user_name",
        "get_global_actions_for_user": "cms.permissions.utils.get_global_actions_for_user",
        "get_model_permission_codename": "cms.permissions.utils.get_model_permission_codename",
        "get_page_actions_for_user": "cms.permissions.utils.get_page_actions_for_user",
        "get_permission_codename": "django.contrib.auth.get_permission_codename",
        "get_subordinate_groups": "cms.permissions.utils.get_subordinate_groups",
        "get_subordinate_users": "cms.permissions.utils.get_subordinate_users",
        "get_user_model": "cms.permissions.utils.get_user_model",
        "get_user_permission_level": "cms.permissions.utils.get_user_permission_level",
        "has_global_permission": "cms.permissions.utils.has_global_permission",
        "has_plugin_permission": "cms.permissions.utils.has_plugin_permission",
        "lru_cache": "cms.permissions.utils.lru_cache",
        "reset_current_user": "cms.permissions.utils.reset_current_user",
        "set_current_user": "cms.permissions.utils.set_current_user",
        "user_can_add_global_permissions": "cms.permissions.utils.user_can_add_global_permissions",
        "user_can_change_global_permissions": "cms.permissions.utils.user_can_change_global_permissions",
        "user_can_delete_global_permissions": "cms.permissions.utils.user_can_delete_global_permissions",
        "user_can_view_placeholder_source": "cms.permissions.utils.user_can_view_placeholder_source",
        "wraps": "cms.permissions.utils.wraps",
    },
    since="6.0",
    fallback="cms.permissions.utils",
)
