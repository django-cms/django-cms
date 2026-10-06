"""The core checks extension operations run, registered with :mod:`cms.shared.checks`.

Each check takes the service's arguments as keywords: the ``extension``, whose
``extended_object`` is the page or page content it extends, and ``permissions``,
the page permission backend a caller handed to the service, or ``None`` for the
default one.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.core.checks import register_editable_operation
from cms.extensions.models import PageContentExtension
from cms.pages.permissions import get_page_permissions
from cms.shared.checks import PERMISSION, VALIDATION, register_core_check

CHANGE_DENIED = _("You do not have permission to change this page.")


def _permissions(permissions, context):
    return permissions if permissions is not None else get_page_permissions(context.user)


def check_extension_permission(context, *, extension, permissions=None, **kwargs):
    """Changing an extension is changing what it extends: the page, or one translation of it."""
    permissions = _permissions(permissions, context)
    extended = extension.extended_object
    if isinstance(extension, PageContentExtension):
        allowed = permissions.can_change_content(extended)
    else:
        allowed = permissions.can_change_page(extended)
    if not allowed:
        raise PermissionDenied(CHANGE_DENIED)


def check_one_extension_per_object(context, *, extension, **kwargs):
    if extension.pk is None and type(extension).objects.filter(extended_object=extension.extended_object).exists():
        raise ValidationError(_("This object already has this extension."))


for _operation in (operations.SAVE_EXTENSION, operations.DELETE_EXTENSION):
    register_core_check(
        _operation,
        "cms.extensions.change_permission",
        check_extension_permission,
        kind=PERMISSION,
        requires=["extension"],
    )
register_core_check(
    operations.SAVE_EXTENSION,
    "cms.extensions.one_per_object",
    check_one_extension_per_object,
    kind=VALIDATION,
    requires=["extension"],
)


# A page content extension is part of its translation's content: changing it
# runs the editability checks for the translation (cms.core.checks).


def _extended_content(extension, **kwargs):
    return [extension.extended_object] if isinstance(extension, PageContentExtension) else []


for _operation in (operations.SAVE_EXTENSION, operations.DELETE_EXTENSION):
    register_editable_operation(_operation, _extended_content, requires=["extension"])
