"""Saving and deleting page and page content extensions, callable without an HttpRequest.

An extension belongs to what it extends, so changing it is changing the page or
the translation: the checks (:mod:`cms.extensions.checks`) ask the page
permission backend (:mod:`cms.pages.permissions`), and the operations are
announced with the page operation signals, ``obj`` being the page and, for a
page content extension, ``translation`` the page content.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _lazy

from cms import operations
from cms.extensions import checks as extension_checks  # noqa: F401  -- registers the extension checks
from cms.extensions.models import BaseExtension, PageContentExtension
from cms.models import Page
from cms.operations import Operation, register_operation
from cms.shared.operations import OperationContext, operation
from cms.signals import PAGE_OPERATION_SIGNALS

__all__ = ["delete_extension", "save_extension"]


def _signal_kwargs(extension):
    kwargs = {"obj": extension.get_page(), "extension": extension}
    if isinstance(extension, PageContentExtension):
        kwargs["translation"] = extension.extended_object
    return kwargs


def save_extension(extension: BaseExtension, *, context: OperationContext, permissions=None) -> BaseExtension:
    """Save a new or changed extension. ``extension.extended_object`` must be set.

    :raises ~django.core.exceptions.PermissionDenied: if the acting user may not change what it extends.
    :raises ~django.core.exceptions.ValidationError: if a new extension's object already has one.
    """
    with operation(
        operations.SAVE_EXTENSION,
        context,
        checks={"extension": extension, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        **_signal_kwargs(extension),
    ):
        extension.save()
    return extension


def delete_extension(extension: BaseExtension, *, context: OperationContext, permissions=None) -> None:
    """Delete an extension.

    :raises ~django.core.exceptions.PermissionDenied: if the acting user may not change what it extends.
    """
    with operation(
        operations.DELETE_EXTENSION,
        context,
        checks={"extension": extension, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        **_signal_kwargs(extension),
    ):
        extension.delete()


# -- operation registry -------------------------------------------------------
# Summaries are shown to editors and translated; descriptions are read by API
# schemas and assistant tool definitions and stay plain English.

for _declaration in (
    Operation(
        operations.SAVE_EXTENSION,
        summary=_lazy("Save a page extension"),
        description=(
            "Create or change an extension of a page or of one translation of a page. Requires "
            "permission to change the page or the translation. Refused for a second extension of the "
            "same kind on the same object."
        ),
        service=save_extension,
    ),
    Operation(
        operations.DELETE_EXTENSION,
        summary=_lazy("Delete a page extension"),
        description=(
            "Delete an extension of a page or of one translation of a page. Requires permission to "
            "change the page or the translation."
        ),
        service=delete_extension,
    ),
):
    register_operation(_declaration)
del _declaration
