"""Moved to :mod:`cms.pages.admin.forms`.

Kept importable because third-party packages subclass these by this path
(see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "AddPageForm": "cms.pages.admin.forms.AddPageForm",
        "AddPageTypeForm": "cms.pages.admin.forms.AddPageTypeForm",
        "AdvancedSettingsForm": "cms.pages.admin.forms.AdvancedSettingsForm",
        "BasePageContentForm": "cms.pages.admin.forms.BasePageContentForm",
        "BasePermissionAdminForm": "cms.pages.admin.forms.BasePermissionAdminForm",
        "CMS_PERMISSION_ACTIONS": "cms.pages.admin.forms.CMS_PERMISSION_ACTIONS",
        "CMS_PERMISSION_MODELS": "cms.pages.admin.forms.CMS_PERMISSION_MODELS",
        "ChangeListForm": "cms.pages.admin.forms.ChangeListForm",
        "ChangePageForm": "cms.pages.admin.forms.ChangePageForm",
        "CopyPageForm": "cms.pages.admin.forms.CopyPageForm",
        "CopyPermissionForm": "cms.pages.admin.forms.CopyPermissionForm",
        "DuplicatePageForm": "cms.pages.admin.forms.DuplicatePageForm",
        "GenericCmsPermissionForm": "cms.pages.admin.forms.GenericCmsPermissionForm",
        "GlobalPagePermissionAdminForm": "cms.pages.admin.forms.GlobalPagePermissionAdminForm",
        "MovePageForm": "cms.pages.admin.forms.MovePageForm",
        "PagePermissionInlineAdminForm": "cms.pages.admin.forms.PagePermissionInlineAdminForm",
        "PageTreeForm": "cms.pages.admin.forms.PageTreeForm",
        "PageUserAddForm": "cms.pages.admin.forms.PageUserAddForm",
        "PageUserChangeForm": "cms.pages.admin.forms.PageUserChangeForm",
        "PageUserGroupForm": "cms.pages.admin.forms.PageUserGroupForm",
        "PluginAddValidationForm": "cms.core.admin.forms.PluginAddValidationForm",
        "RequestToolbarForm": "cms.core.admin.forms.RequestToolbarForm",
        "SlugWidget": "cms.pages.admin.forms.SlugWidget",
        "ViewRestrictionInlineAdminForm": "cms.pages.admin.forms.ViewRestrictionInlineAdminForm",
        "get_main_language_page_content_template": "cms.pages.admin.forms.get_main_language_page_content_template",
        "get_page_changed_by_filter_choices": "cms.pages.admin.forms.get_page_changed_by_filter_choices",
        "get_page_template_filter_choices": "cms.pages.admin.forms.get_page_template_filter_choices",
        "get_permission_accessor": "cms.pages.admin.forms.get_permission_accessor",
        "save_permissions": "cms.pages.admin.forms.save_permissions",
    },
    since="6.0",
    fallback="cms.pages.admin.forms",
)
