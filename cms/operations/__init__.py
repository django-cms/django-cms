"""The operation registry.

Every operation that changes content is declared here once, as an
:class:`Operation`: a stable ``id`` -- the constants below are these ids, and the
names the operation signals carry -- a one-line ``summary`` for people, a
plain-English ``description`` for programs and developers, and the ``service``
performing it. Checks, signals, log entries and dry runs refer to an operation by
its id; log entries, API schemas and tool definitions read the summary and
description from here instead of writing their own.

The summary is shown to editors, so it is translatable: declare it with
``gettext_lazy``. The description is read by API schemas and assistant tool
definitions, which rely on stable wording, so it is plain English and not
translated; it defaults to the service's docstring.

Core parts declare their operations next to their services. Apps declare theirs
in their ``cms_config``::

    class MyAppConfig(CMSAppConfig):
        cms_operations = [
            Operation("myapp.publish", summary=_("Publish an article"), service=publish),
        ]
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from typing import Any

__all__ = ["Operation", "get_operation", "get_operations", "register_operation"]


@dataclass(frozen=True)
class Operation:
    """The declaration of an operation."""

    #: Stable and unique, e.g. ``"move_plugin"``. Used as the OpenAPI ``operationId``.
    id: str
    #: One line, shown to people. Translatable (``gettext_lazy``).
    summary: Any
    #: Plain English: what changes, what is required, what may refuse it. Not
    #: translated. Defaults to the service's docstring.
    description: str = ""
    #: The service performing the operation, if it has one.
    service: Callable | None = None


_registry: dict[str, Operation] = {}


def register_operation(declaration: Operation) -> Operation:
    """Declare an operation. Its id must not be declared yet.

    Returns the declaration as registered, with the description taken from the
    service's docstring if none was given.
    """
    if not declaration.id:
        raise ValueError("An operation needs an id.")
    if not declaration.summary:
        raise ValueError(f"Operation {declaration.id!r} needs a summary.")
    if declaration.id in _registry:
        raise ValueError(f"Operation {declaration.id!r} is already declared.")
    if not declaration.description and declaration.service is not None:
        declaration = replace(declaration, description=inspect.getdoc(declaration.service) or "")
    _registry[declaration.id] = declaration
    return declaration


def get_operation(operation_id: str) -> Operation:
    """The declaration of ``operation_id``. Raises ``LookupError`` if there is none."""
    try:
        return _registry[operation_id]
    except KeyError:
        raise LookupError(f"Operation {operation_id!r} is not declared.") from None


def get_operations() -> Iterator[Operation]:
    """Every declared operation, in the order they were declared."""
    return iter(list(_registry.values()))


# Placeholder operations
ADD_PLUGIN = 'add_plugin'
CHANGE_PLUGIN = 'change_plugin'
DELETE_PLUGIN = 'delete_plugin'
MOVE_PLUGIN = 'move_plugin'
CUT_PLUGIN = 'cut_plugin'
PASTE_PLUGIN = 'paste_plugin'
PASTE_PLACEHOLDER = 'paste_placeholder'
ADD_PLUGINS_FROM_PLACEHOLDER = 'add_plugins_from_placeholder'
CLEAR_PLACEHOLDER = 'clear_placeholder'
COPY_PLUGIN_TO_CLIPBOARD = 'copy_plugin_to_clipboard'
COPY_PLACEHOLDER_TO_CLIPBOARD = 'copy_placeholder_to_clipboard'

# Page operations
CHANGE_PAGE = 'change_page'
ADD_PAGE = 'add_page'
CHANGE_PAGE_ADVANCED_SETTINGS = 'change_page_advanced_settings'
CHANGE_PAGE_PERMISSIONS = 'change_page_permissions'
CHANGE_GLOBAL_PAGE_PERMISSION = 'change_global_page_permission'
DELETE_GLOBAL_PAGE_PERMISSION = 'delete_global_page_permission'
CHANGE_USER_PERMISSIONS = 'change_user_permissions'
MOVE_PAGE = 'move_page'
DELETE_PAGE = 'delete_page'
SET_HOME = 'set_home'
COPY_PAGE = 'copy_page'
COPY_PAGE_FROM_SOURCE = 'copy_page_from_source'

# Page translation operations
ADD_PAGE_TRANSLATION = 'add_page_translation'
CHANGE_PAGE_TRANSLATION = 'change_page_translation'
DELETE_PAGE_TRANSLATION = 'delete_page_translation'
PUBLISH_PAGE_TRANSLATION = 'publish_page_translation'
REVERT_PAGE_TRANSLATION_TO_LIVE = 'revert_page_translation_to_live'
CHANGE_PAGE_TEMPLATE = 'change_page_template'
COPY_PAGE_LANGUAGE = 'copy_page_language'
TOGGLE_PAGE_IN_NAVIGATION = 'toggle_page_in_navigation'

# Static placeholder operations
PUBLISH_STATIC_PLACEHOLDER = 'publish_static_placeholder'

PAGE_OPERATIONS = [MOVE_PAGE, DELETE_PAGE, SET_HOME, COPY_PAGE]
PAGE_TRANSLATION_OPERATIONS = [
    DELETE_PAGE_TRANSLATION,
    PUBLISH_PAGE_TRANSLATION,
    REVERT_PAGE_TRANSLATION_TO_LIVE,
    CHANGE_PAGE_TEMPLATE,
    COPY_PAGE_LANGUAGE,
    TOGGLE_PAGE_IN_NAVIGATION,
]
STATIC_PLACEHOLDER_OPERATIONS = [PUBLISH_STATIC_PLACEHOLDER]
