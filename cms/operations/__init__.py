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

The ``arguments`` describe what a caller outside Python -- a REST endpoint, an
MCP tool -- supplies, as :class:`Argument` declarations; :meth:`Operation.json_schema`
turns them into the JSON Schema both use. Declared arguments are checked against
the service's signature when the operation is declared. An operation without
``arguments`` is left out by such adapters.

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

__all__ = ["Argument", "Operation", "get_operation", "get_operations", "register_operation"]

#: Service parameters that are never arguments: the acting context, a
#: permission backend replacing the default for one call, and the signal sender.
RESERVED_PARAMETERS = frozenset({"context", "permissions", "sender"})

_JSON_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array",
    object: "object",
}


@dataclass(frozen=True)
class Argument:
    """One argument of an operation, as a caller outside Python supplies it.

    An argument is either a value -- ``type`` is ``str``, ``int``, ``float``,
    ``bool``, ``dict``, ``list`` or ``object``, or a tuple of them -- or an
    object of a ``model``, named by its label (``"cms.Page"``) or a tuple of
    labels. A model argument names a stored object by primary key, which the
    adapter resolves for the acting user; with ``instance`` it is an object the
    caller builds instead -- a new one, or a stored one with changed fields.
    """

    #: The service's keyword argument.
    name: str
    #: The value's type, for an argument that is not a model object.
    type: Any = None
    #: Plain English, for API schemas and tool definitions. Not translated.
    description: str = ""
    #: The label of the model, for a model object.
    model: str | tuple[str, ...] | None = None
    required: bool = True
    #: ``None`` is a valid value (e.g. no parent page: the root of the site).
    null: bool = False
    #: A list of values or objects.
    many: bool = False
    #: The values allowed.
    choices: tuple = ()
    #: The caller builds the model object rather than naming a stored one.
    instance: bool = False

    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"Argument name {self.name!r} is not an identifier.")
        if (self.type is None) == (self.model is None):
            raise ValueError(f"Argument {self.name!r} needs either a type or a model.")
        types = self.type if isinstance(self.type, tuple) else (self.type,)
        if self.type is not None and any(value not in _JSON_TYPES for value in types):
            raise ValueError(f"Argument {self.name!r} has a type JSON cannot carry: {self.type!r}.")
        if self.instance and self.model is None:
            raise ValueError(f"Argument {self.name!r} is an instance, but of no model.")
        object.__setattr__(self, "choices", tuple(self.choices))

    @property
    def models(self) -> tuple[str, ...]:
        """The model labels, lower case as Django's ``Options.label_lower``."""
        if self.model is None:
            return ()
        labels = (self.model,) if isinstance(self.model, str) else self.model
        return tuple(label.lower() for label in labels)

    def json_schema(self) -> dict:
        """The JSON Schema of the argument's value.

        A model object is its primary key, marked with the model's label as
        ``x-cms-model``; a built instance is an object, marked as well.
        """
        if self.model is not None:
            schema = {"type": "object" if self.instance else ["integer", "string"]}
            models = self.models
            schema["x-cms-model"] = models[0] if len(models) == 1 else list(models)
            if self.instance:
                schema["x-cms-instance"] = True
        else:
            types = self.type if isinstance(self.type, tuple) else (self.type,)
            names = list(dict.fromkeys(_JSON_TYPES[value] for value in types))
            schema = {"type": names[0] if len(names) == 1 else names}
        if self.choices:
            schema["enum"] = list(self.choices)
        if self.many:
            schema = {"type": "array", "items": schema}
        if self.null:
            schema = {"anyOf": [schema, {"type": "null"}]}
        if self.description:
            schema["description"] = self.description
        return schema


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
    #: What a caller supplies, see :class:`Argument`. ``None``: not declared.
    arguments: tuple[Argument, ...] | None = None

    def __post_init__(self):
        if self.arguments is not None:
            object.__setattr__(self, "arguments", tuple(self.arguments))

    def json_schema(self) -> dict | None:
        """The JSON Schema of the arguments, for a REST request body or an MCP ``inputSchema``.

        ``None`` if the operation declares no arguments.
        """
        if self.arguments is None:
            return None
        schema = {
            "type": "object",
            "properties": {argument.name: argument.json_schema() for argument in self.arguments},
            "additionalProperties": False,
        }
        required = [argument.name for argument in self.arguments if argument.required]
        if required:
            schema["required"] = required
        return schema


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
    if declaration.arguments is not None:
        _check_arguments(declaration)
    if not declaration.description and declaration.service is not None:
        declaration = replace(declaration, description=inspect.getdoc(declaration.service) or "")
    _registry[declaration.id] = declaration
    return declaration


def _check_arguments(declaration: Operation) -> None:
    """Raise ``ValueError`` unless the arguments fit the service's signature.

    Every argument must be a keyword argument of the service -- an adapter calls
    the service, and :func:`~cms.shared.checks.can`, with the arguments as
    keywords -- and every parameter the service requires must be declared.
    """
    names = [argument.name for argument in declaration.arguments]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Operation {declaration.id!r} declares {', '.join(duplicates)} more than once.")
    reserved = sorted(RESERVED_PARAMETERS.intersection(names))
    if reserved:
        raise ValueError(f"Operation {declaration.id!r} declares {', '.join(reserved)}, which callers never supply.")
    if declaration.service is None:
        return
    parameters = inspect.signature(declaration.service).parameters
    keywords = {
        name: parameter
        for name, parameter in parameters.items()
        if parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    any_keyword = any(parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values())
    for argument in declaration.arguments:
        parameter = keywords.get(argument.name)
        if parameter is None:
            if not any_keyword:
                raise ValueError(
                    f"Operation {declaration.id!r} declares {argument.name!r}, "
                    f"which its service does not take as a keyword argument."
                )
        elif not argument.required and parameter.default is inspect.Parameter.empty:
            raise ValueError(
                f"Operation {declaration.id!r} declares {argument.name!r} optional, but its service requires it."
            )
    for name, parameter in parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if name in RESERVED_PARAMETERS or parameter.default is not inspect.Parameter.empty:
            continue
        if name not in names:
            raise ValueError(f"The service of operation {declaration.id!r} requires {name!r}, which is not declared.")


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

# Page and page content extensions
SAVE_EXTENSION = 'save_extension'
DELETE_EXTENSION = 'delete_extension'

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
