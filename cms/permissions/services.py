"""Granting and revoking CMS permissions, callable without an HttpRequest.

These operations change *who may act*, not content: the permission grants of a
page, site-wide (global) page permissions, and the CMS model permissions of users
and groups. Each runs its checks (:mod:`cms.permissions.checks`) in the
:func:`~cms.shared.operations.operation` frame, so that nobody hands out more
than they hold. Code acting on the system's own behalf, such as :mod:`cms.api`,
passes ``OperationContext.system()`` and skips those checks.
"""

from __future__ import annotations

from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.translation import gettext_lazy as _lazy

from cms import operations
from cms.operations import Operation, register_operation
from cms.permissions.checks import CMS_PERMISSION_ACTIONS, cms_permission_models
from cms.permissions.models import PageUser, PageUserGroup
from cms.shared.operations import OperationContext, operation

__all__ = [
    "delete_global_page_permission",
    "delete_global_page_permissions",
    "permission_accessor",
    "save_global_page_permission",
    "save_page_permissions",
    "set_user_permissions",
]



def permission_accessor(obj):
    """The Django auth permission relation of a CMS user or group."""
    from cms.permissions.models import User

    return getattr(obj, "user_permissions" if isinstance(obj, (PageUser, User)) else "permissions")


@transaction.atomic
def set_user_permissions(data, obj, *, context: OperationContext):
    """Apply the CMS model permission fields in ``data`` to a user or group.

    ``data`` maps ``can_<action>_<name>`` fields to booleans; a field that is
    missing is left as it is. The ``CHANGE_USER_PERMISSIONS``
    checks make sure the acting user manages ``obj`` and holds every permission
    they set or clear. :mod:`cms.api` passes ``OperationContext.system()``.

    :raises ~django.core.exceptions.PermissionDenied: if the acting user may not.
    """
    with operation(operations.CHANGE_USER_PERMISSIONS, context, checks={"obj": obj, "data": data}):
        if not obj.pk:
            obj.save()
        accessor = permission_accessor(obj)
        for model, name in (*cms_permission_models(), (PageUserGroup, "pageuser")):
            content_type = ContentType.objects.get_for_model(model)
            for action in CMS_PERMISSION_ACTIONS:
                field = f"can_{action}_{name}"
                if field not in data:
                    continue
                codename = get_permission_codename(action, model._meta)
                permission = Permission.objects.get(content_type=content_type, codename=codename)
                if data[field]:
                    accessor.add(permission)
                else:
                    accessor.remove(permission)
    return obj


@transaction.atomic
def save_page_permissions(page, *, save=(), delete=(), context: OperationContext, permissions=None):
    """Save and delete the page permission grants of one page.

    :raises ~django.core.exceptions.PermissionDenied: if the acting user may not
        change the page's permissions, or not grant a flag set on a saved grant.
    :raises ~django.core.exceptions.ValidationError: if a grant belongs to another page.
    """
    save, delete = list(save), list(delete)
    with operation(
        operations.CHANGE_PAGE_PERMISSIONS,
        context,
        checks={"page": page, "save": save, "delete": delete, "permissions": permissions},
    ):
        for grant in delete:
            grant.delete()
        for grant in save:
            grant.page = page
            grant.save()


@transaction.atomic
def save_global_page_permission(grant, *, sites, context: OperationContext):
    """Save a site-wide page grant for ``sites``.

    The ``CHANGE_GLOBAL_PAGE_PERMISSION`` checks compare both
    the stored grant and the new one with what the acting user may hand out.

    :raises ~django.core.exceptions.PermissionDenied: if the acting user may not.
    """
    sites = list(sites)
    with operation(
        operations.CHANGE_GLOBAL_PAGE_PERMISSION, context, checks={"grant": grant, "sites": sites}
    ):
        grant.save()
        grant.sites.set(sites)
    return grant


@transaction.atomic
def delete_global_page_permission(grant, *, context: OperationContext):
    """Delete a site-wide grant if the acting user could have granted it.

    :raises ~django.core.exceptions.PermissionDenied: if the acting user may not.
    """
    with operation(operations.DELETE_GLOBAL_PAGE_PERMISSION, context, checks={"grant": grant}):
        grant.delete()


@transaction.atomic
def delete_global_page_permissions(grants, *, context: OperationContext):
    """Delete several site-wide grants: all of them, or none if one is refused."""
    for grant in list(grants):
        delete_global_page_permission(grant, context=context)


# -- operation registry -------------------------------------------------------
# Summaries are shown to editors and translated; descriptions are read by API
# schemas and assistant tool definitions and stay plain English.

for _declaration in (
    Operation(
        operations.CHANGE_PAGE_PERMISSIONS,
        summary=_lazy("Change a page's permissions"),
        description=(
            "Save and delete the permission grants of a page. Requires permission to change the "
            "page's permissions; editing rights can only be granted to users and groups the acting "
            "user manages, and only with flags the acting user holds."
        ),
        service=save_page_permissions,
    ),
    Operation(
        operations.CHANGE_USER_PERMISSIONS,
        summary=_lazy("Change a user's or group's permissions"),
        description=(
            "Set the django CMS model permissions of a user or group. Requires that the acting user "
            "manages that user or group and holds every permission set or cleared."
        ),
        service=set_user_permissions,
    ),
    Operation(
        operations.CHANGE_GLOBAL_PAGE_PERMISSION,
        summary=_lazy("Change a global page permission"),
        description=(
            "Save a page permission that applies to every page of its sites. The acting user must "
            "hold every flag of the grant on its sites."
        ),
        service=save_global_page_permission,
    ),
    Operation(
        operations.DELETE_GLOBAL_PAGE_PERMISSION,
        summary=_lazy("Delete a global page permission"),
        description=(
            "Delete a page permission that applies to every page of its sites. The acting user must "
            "be able to have granted it."
        ),
        service=delete_global_page_permission,
    ),
):
    register_operation(_declaration)
del _declaration
