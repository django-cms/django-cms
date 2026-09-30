"""The core checks for granting CMS permissions, registered with :mod:`cms.shared.checks`.

They guard the grants themselves -- global page permissions and the CMS model
permissions of users and groups -- so that nobody hands out more than they hold.
All of them are permission checks: :mod:`cms.api` and other system callers
(``OperationContext.system()``) skip them.
"""

from __future__ import annotations

from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.permissions.models import GlobalPagePermission, PagePermission, PageUser
from cms.shared.checks import PERMISSION, register_core_check

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
