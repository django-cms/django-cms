"""The core checks for granting CMS permissions, registered with :mod:`cms.shared.checks`.

They guard the grants themselves -- the permissions of a page, global page
permissions and the CMS model permissions of users and groups -- so that nobody
hands out more than they hold. Apart from ``cms.permissions.grants_belong_to_page``
they are permission checks: :mod:`cms.api` and other system callers
(``OperationContext.system()``) skip them.
"""

from __future__ import annotations

from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.permissions.models import GlobalPagePermission, PagePermission, PageUser
from cms.shared.checks import PERMISSION, VALIDATION, register_core_check

#: The CMS model permissions a user or group form manages: ``can_<action>_<name>``.
CMS_PERMISSION_ACTIONS = ("add", "change", "delete")


def cms_permission_models():
    from cms.pages.models.page import Page

    return ((Page, "page"), (PageUser, "pageuser"), (PagePermission, "pagepermission"))


# Users and groups


def check_manage_user_or_group(context, *, obj, **kwargs):
    """Only a user or group the acting user manages may have its permissions changed."""
    user = context.user
    if not obj.pk or (user is not None and user.is_superuser):
        return
    if user is None:
        raise PermissionDenied(_("You may not manage this user or group."))
    from cms.permissions.utils import get_subordinate_groups, get_subordinate_users

    site = Site.objects.get_current(context.request)
    subordinates = (
        get_subordinate_users(user, site) if isinstance(obj, PageUser) else get_subordinate_groups(user, site)
    )
    if not subordinates.filter(pk=obj.pk).exists():
        raise PermissionDenied(_("You may not manage this user or group."))


def check_grantable_user_permissions(context, *, data, **kwargs):
    """Every permission field set or cleared must be one the acting user holds."""
    user = context.user
    for model, name in cms_permission_models():
        for action in CMS_PERMISSION_ACTIONS:
            if f"can_{action}_{name}" not in data:
                continue
            perm = f"{model._meta.app_label}.{get_permission_codename(action, model._meta)}"
            if user is None or not user.has_perm(perm):
                raise PermissionDenied(_("You may not manage this permission."))


register_core_check(
    operations.CHANGE_USER_PERMISSIONS,
    "cms.permissions.manage_user_or_group",
    check_manage_user_or_group,
    kind=PERMISSION,
    requires=["obj"],
)
register_core_check(
    operations.CHANGE_USER_PERMISSIONS,
    "cms.permissions.grantable_user_permissions",
    check_grantable_user_permissions,
    kind=PERMISSION,
    requires=["data"],
)


# Global page permissions


def global_grant_allowed(grant, site_ids, user) -> bool:
    """May ``user`` manage ``grant`` with its flags on ``site_ids``?"""
    if user is None:
        return False
    from cms.permissions.utils import get_grantable_global_permissions

    grantable = get_grantable_global_permissions(user, site_ids)
    held = {flag for flag in GlobalPagePermission.get_all_permissions() if getattr(grant, flag)}
    return "can_change_permissions" in grantable and held <= grantable


def _stored_scope(grant):
    stored = GlobalPagePermission.objects.get(pk=grant.pk)
    return stored, list(stored.sites.values_list("pk", flat=True))


def check_global_grant_manageable(context, *, grant, **kwargs):
    """An existing grant may only be changed by someone who could have granted it."""
    if grant.pk:
        stored, site_ids = _stored_scope(grant)
        if not global_grant_allowed(stored, site_ids, context.user):
            raise PermissionDenied(_("You may not change this global page permission."))


def check_global_grant_grantable(context, *, grant, sites, **kwargs):
    """The grant as saved may only hold flags the acting user holds on its sites."""
    if not global_grant_allowed(grant, [site.pk for site in sites], context.user):
        raise PermissionDenied(_("You may not grant these global page permissions."))


def check_global_grant_deletable(context, *, grant, **kwargs):
    _stored, site_ids = _stored_scope(grant)
    if not global_grant_allowed(grant, site_ids, context.user):
        raise PermissionDenied(_("You may not delete this global page permission."))


register_core_check(
    operations.CHANGE_GLOBAL_PAGE_PERMISSION,
    "cms.permissions.global_grant_manageable",
    check_global_grant_manageable,
    kind=PERMISSION,
    requires=["grant"],
)
register_core_check(
    operations.CHANGE_GLOBAL_PAGE_PERMISSION,
    "cms.permissions.global_grant_grantable",
    check_global_grant_grantable,
    kind=PERMISSION,
    requires=["grant", "sites"],
)
register_core_check(
    operations.DELETE_GLOBAL_PAGE_PERMISSION,
    "cms.permissions.global_grant_deletable",
    check_global_grant_deletable,
    kind=PERMISSION,
    requires=["grant"],
)


# Page permissions


def _page_permissions(permissions, context):
    from cms.pages.permissions import get_page_permissions

    return permissions if permissions is not None else get_page_permissions(context.user)


def check_page_permissions_permission(context, *, page, permissions=None, **kwargs):
    if not _page_permissions(permissions, context).can_change_page_permissions(page):
        raise PermissionDenied(_("You do not have permission to change page permissions."))


register_core_check(
    operations.CHANGE_PAGE_PERMISSIONS,
    "cms.permissions.change_page_permissions",
    check_page_permissions_permission,
    kind=PERMISSION,
    requires=["page"],
)


def check_grants_belong_to_page(context, *, page, save=(), delete=(), **kwargs):
    """Grants to save are new or this page's; grants to delete are this page's."""
    if any(grant.page_id not in (None, page.pk) for grant in save) or any(
        grant.page_id != page.pk for grant in delete
    ):
        raise ValidationError(_("The permission belongs to another page."))


def check_grantable_page_permissions(context, *, page, save=(), **kwargs):
    """Every flag set on a saved grant must be one the acting user holds on the page."""
    held = {
        "can_add": page.has_add_permission,
        "can_change": page.has_change_permission,
        "can_delete": page.has_delete_permission,
        "can_publish": page.has_publish_permission,
        "can_change_advanced_settings": page.has_advanced_settings_permission,
        "can_change_permissions": page.has_change_permissions_permission,
        "can_move_page": page.has_move_page_permission,
        "can_view": page.has_view_permission,
    }
    for grant in save:
        for flag, has_permission in held.items():
            if getattr(grant, flag) and not has_permission(context.user):
                raise PermissionDenied(_("You may not grant this page permission."))


register_core_check(
    operations.CHANGE_PAGE_PERMISSIONS,
    "cms.permissions.grants_belong_to_page",
    check_grants_belong_to_page,
    kind=VALIDATION,
    requires=["page"],
)
register_core_check(
    operations.CHANGE_PAGE_PERMISSIONS,
    "cms.permissions.grantable_page_permissions",
    check_grantable_page_permissions,
    kind=PERMISSION,
    requires=["page"],
)


def check_grant_recipients(context, *, page, save=(), **kwargs):
    """Editing rights may only go to users and groups the acting user manages.

    Mirrors the choices ``PagePermissionInlineAdminForm`` offers. View
    restrictions (grants with ``can_view`` only) have no such limit in the admin
    and have none here.
    """
    user = context.user
    if user is None or user.is_superuser:
        return
    edit_flags = [flag for flag in PagePermission.get_all_permissions() if flag != "can_view"]
    grants = [grant for grant in save if any(getattr(grant, flag) for flag in edit_flags)]
    if not grants:
        return
    from cms.permissions.utils import get_subordinate_groups, get_subordinate_users

    user_ids = {grant.user_id for grant in grants if grant.user_id is not None}
    group_ids = {grant.group_id for grant in grants if grant.group_id is not None}
    allowed_users = (
        set(get_subordinate_users(user, page.site).filter(pk__in=user_ids).values_list("pk", flat=True))
        if user_ids else set()
    )
    allowed_groups = (
        set(get_subordinate_groups(user, page.site).filter(pk__in=group_ids).values_list("pk", flat=True))
        if group_ids else set()
    )
    if user_ids - allowed_users or group_ids - allowed_groups:
        raise PermissionDenied(_("You may not grant page permissions to this user or group."))


register_core_check(
    operations.CHANGE_PAGE_PERMISSIONS,
    "cms.permissions.grant_recipients",
    check_grant_recipients,
    kind=PERMISSION,
    requires=["page"],
)
