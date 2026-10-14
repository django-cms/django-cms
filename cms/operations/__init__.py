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
``arguments`` is left out by such adapters. ``returns`` describes what the
service returns, as a :class:`Result`, so that an adapter can describe its
response.

Reads are declared the same way, as a :class:`Query`: an id, a summary, a
description, the read service, its arguments and its result. Reads change
nothing, so they have no checks, signals or transaction; a REST interface turns
both kinds of declaration into its OpenAPI schema, an MCP server into tools and
resource templates.

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

__all__ = [
    "Argument",
    "Operation",
    "Query",
    "Result",
    "get_operation",
    "get_operations",
    "get_queries",
    "get_query",
    "register_operation",
    "register_query",
]

#: Service parameters that are never arguments: the acting context, a
#: permission backend replacing the default for one call, and the signal sender.
RESERVED_PARAMETERS = frozenset({"context", "permissions", "sender"})

#: Read service parameters that are never arguments: the context, and ``admin``,
#: which an adapter sets from the mode it reads in (see :attr:`Query.modes`).
RESERVED_QUERY_PARAMETERS = frozenset({"context", "admin"})

#: The modes a read may support: what the site shows, and what an editor sees.
QUERY_MODES = ("published", "editing")

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
class Result:
    """What a service returns, for an adapter to describe its response.

    One of: a value (``type``, as for :class:`Argument`), a model object
    (``model``, a label or a tuple of labels) that the adapter serializes, or an
    object with named ``fields``, each a :class:`Result` (a dataclass such as
    :class:`~cms.core.queries.PlaceholderContent`). ``Result()`` with none of
    them: the service returns nothing.
    """

    #: Plain English, for API schemas and tool definitions. Not translated.
    description: str = ""
    type: Any = None
    model: str | tuple[str, ...] | None = None
    #: Name -> :class:`Result`, for an object with named fields.
    fields: Any = ()
    #: A list.
    many: bool = False
    #: ``None`` is a possible value.
    null: bool = False

    def __post_init__(self):
        fields = tuple(self.fields.items()) if isinstance(self.fields, dict) else tuple(self.fields)
        object.__setattr__(self, "fields", fields)
        if sum(bool(part) for part in (self.type is not None, self.model is not None, fields)) > 1:
            raise ValueError("A result is a value, a model object or an object with fields, not several.")
        types = self.type if isinstance(self.type, tuple) else (self.type,)
        if self.type is not None and any(value not in _JSON_TYPES for value in types):
            raise ValueError(f"A result has a type JSON cannot carry: {self.type!r}.")
        if any(not isinstance(value, Result) for _, value in fields):
            raise ValueError("Every field of a result is a Result.")

    @property
    def is_empty(self) -> bool:
        """The service returns nothing."""
        return self.type is None and self.model is None and not self.fields

    @property
    def models(self) -> tuple[str, ...]:
        """The model labels, lower case as Django's ``Options.label_lower``."""
        if self.model is None:
            return ()
        labels = (self.model,) if isinstance(self.model, str) else self.model
        return tuple(label.lower() for label in labels)

    def json_schema(self) -> dict:
        """The JSON Schema of the result.

        A model object is an object marked with its label as ``x-cms-model``: its
        fields are the adapter's serializer's to describe. Nothing is ``null``.
        """
        if self.is_empty:
            schema = {"type": "null"}
        elif self.fields:
            schema = {
                "type": "object",
                "properties": {name: value.json_schema() for name, value in self.fields},
                "required": [name for name, _ in self.fields],
            }
        elif self.model is not None:
            models = self.models
            schema = {"type": "object", "x-cms-model": models[0] if len(models) == 1 else list(models)}
        else:
            types = self.type if isinstance(self.type, tuple) else (self.type,)
            names = list(dict.fromkeys(_JSON_TYPES[value] for value in types))
            schema = {"type": names[0] if len(names) == 1 else names}
        if self.many:
            schema = {"type": "array", "items": schema}
        if self.null and not self.is_empty:
            schema = {"anyOf": [schema, {"type": "null"}]}
        if self.description:
            schema["description"] = self.description
        return schema


def _arguments_schema(arguments) -> dict | None:
    if arguments is None:
        return None
    schema = {
        "type": "object",
        "properties": {argument.name: argument.json_schema() for argument in arguments},
        "additionalProperties": False,
    }
    required = [argument.name for argument in arguments if argument.required]
    if required:
        schema["required"] = required
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
    #: What the service returns, see :class:`Result`. ``None``: not declared.
    returns: Result | None = None

    def __post_init__(self):
        if self.arguments is not None:
            object.__setattr__(self, "arguments", tuple(self.arguments))

    def json_schema(self) -> dict | None:
        """The JSON Schema of the arguments, for a REST request body or an MCP ``inputSchema``.

        ``None`` if the operation declares no arguments.
        """
        return _arguments_schema(self.arguments)

    def output_schema(self) -> dict | None:
        """The JSON Schema of the result, for a REST response or an MCP ``outputSchema``.

        ``None`` if the operation declares no result.
        """
        return self.returns.json_schema() if self.returns is not None else None


@dataclass(frozen=True)
class Query:
    """The declaration of a read: like an :class:`Operation`, for a read service.

    ``modes`` says which reads the service offers: ``"published"`` -- what the
    site shows -- and ``"editing"`` -- what an editor sees, drafts included. A
    service offering ``"editing"`` takes ``admin=True`` for it; an adapter sets
    ``admin`` from the mode it reads in, so ``admin`` is never an argument.
    """

    #: Stable and unique among operations and queries. Used as the OpenAPI ``operationId``.
    id: str
    #: One line, shown to people. Translatable (``gettext_lazy``).
    summary: Any
    #: Plain English: what is read, who may read it. Not translated. Defaults to
    #: the service's docstring.
    description: str = ""
    #: The read service.
    service: Callable | None = None
    #: What a caller supplies, see :class:`Argument`. ``None``: not declared.
    arguments: tuple[Argument, ...] | None = None
    #: What the service returns, see :class:`Result`. ``None``: not declared.
    returns: Result | None = None
    #: The modes the read supports, from :data:`QUERY_MODES`.
    modes: tuple[str, ...] = ("published",)

    def __post_init__(self):
        if self.arguments is not None:
            object.__setattr__(self, "arguments", tuple(self.arguments))
        object.__setattr__(self, "modes", tuple(self.modes))

    def json_schema(self) -> dict | None:
        """The JSON Schema of the arguments: query or path parameters, an MCP resource template's."""
        return _arguments_schema(self.arguments)

    def output_schema(self) -> dict | None:
        """The JSON Schema of the result. ``None`` if the query declares no result."""
        return self.returns.json_schema() if self.returns is not None else None


_registry: dict[str, Operation] = {}
_queries: dict[str, Query] = {}


def register_operation(declaration: Operation) -> Operation:
    """Declare an operation. Its id must not be declared yet.

    Returns the declaration as registered, with the description taken from the
    service's docstring if none was given.
    """
    if not declaration.id:
        raise ValueError("An operation needs an id.")
    if not declaration.summary:
        raise ValueError(f"Operation {declaration.id!r} needs a summary.")
    if declaration.id in _registry or declaration.id in _queries:
        raise ValueError(f"Operation {declaration.id!r} is already declared.")
    if declaration.arguments is not None:
        _check_arguments(declaration, RESERVED_PARAMETERS, "Operation")
    if not declaration.description and declaration.service is not None:
        declaration = replace(declaration, description=inspect.getdoc(declaration.service) or "")
    _registry[declaration.id] = declaration
    return declaration


def register_query(declaration: Query) -> Query:
    """Declare a read. Its id must not be declared yet, as a query or an operation.

    Returns the declaration as registered, with the description taken from the
    service's docstring if none was given.
    """
    if not declaration.id:
        raise ValueError("A query needs an id.")
    if not declaration.summary:
        raise ValueError(f"Query {declaration.id!r} needs a summary.")
    if declaration.id in _queries or declaration.id in _registry:
        raise ValueError(f"Query {declaration.id!r} is already declared.")
    unknown = [mode for mode in declaration.modes if mode not in QUERY_MODES]
    if not declaration.modes or unknown:
        raise ValueError(f"Query {declaration.id!r} has modes {declaration.modes!r}; choose from {QUERY_MODES!r}.")
    if "editing" in declaration.modes and declaration.service is not None:
        if "admin" not in inspect.signature(declaration.service).parameters:
            raise ValueError(f"Query {declaration.id!r} offers editing reads, but its service takes no 'admin'.")
    if declaration.arguments is not None:
        _check_arguments(declaration, RESERVED_QUERY_PARAMETERS, "Query")
    if not declaration.description and declaration.service is not None:
        declaration = replace(declaration, description=inspect.getdoc(declaration.service) or "")
    _queries[declaration.id] = declaration
    return declaration


def _check_arguments(declaration, reserved_parameters: frozenset, kind: str) -> None:
    """Raise ``ValueError`` unless the arguments fit the service's signature.

    Every argument must be a keyword argument of the service -- an adapter calls
    the service, and :func:`~cms.shared.checks.can`, with the arguments as
    keywords -- and every parameter the service requires must be declared.
    """
    names = [argument.name for argument in declaration.arguments]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"{kind} {declaration.id!r} declares {', '.join(duplicates)} more than once.")
    reserved = sorted(reserved_parameters.intersection(names))
    if reserved:
        raise ValueError(f"{kind} {declaration.id!r} declares {', '.join(reserved)}, which callers never supply.")
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
                    f"{kind} {declaration.id!r} declares {argument.name!r}, "
                    f"which its service does not take as a keyword argument."
                )
        elif not argument.required and parameter.default is inspect.Parameter.empty:
            raise ValueError(
                f"{kind} {declaration.id!r} declares {argument.name!r} optional, but its service requires it."
            )
    for name, parameter in parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if name in reserved_parameters or parameter.default is not inspect.Parameter.empty:
            continue
        if name not in names:
            raise ValueError(
                f"The service of {kind.lower()} {declaration.id!r} requires {name!r}, which is not declared."
            )


def get_operation(operation_id: str) -> Operation:
    """The declaration of ``operation_id``. Raises ``LookupError`` if there is none."""
    try:
        return _registry[operation_id]
    except KeyError:
        raise LookupError(f"Operation {operation_id!r} is not declared.") from None


def get_operations() -> Iterator[Operation]:
    """Every declared operation, in the order they were declared."""
    return iter(list(_registry.values()))


def get_query(query_id: str) -> Query:
    """The declaration of ``query_id``. Raises ``LookupError`` if there is none."""
    try:
        return _queries[query_id]
    except KeyError:
        raise LookupError(f"Query {query_id!r} is not declared.") from None


def get_queries() -> Iterator[Query]:
    """Every declared query, in the order they were declared."""
    return iter(list(_queries.values()))


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
