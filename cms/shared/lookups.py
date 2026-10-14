"""Scoped lookups: the object with this primary key, if the acting user may see it.

An adapter -- a REST endpoint, an MCP tool -- receives primary keys and needs
objects. Which objects a user may see is a container's business, so each
container registers a lookup for its models under the model's label; adapters
call :func:`lookup` with the label an operation's
:class:`~cms.operations.Argument` declares (``Argument.models``) and never query
the models themselves.

A lookup is a callable ``lookup(pk, context, *, admin=False)`` returning the
object, or raising the model's ``DoesNotExist`` when there is no such object *or*
the user may not see it. Missing and hidden are deliberately indistinguishable, so
that a lookup never confirms that content exists to a user who may not see it.

``admin=True`` reads as an editor -- drafts included, for staff users -- which is
what an adapter resolving the arguments of a write needs; ``admin=False`` reads
what the site shows.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

__all__ = ["get_lookup", "lookup", "lookup_many", "register_lookup"]

_lookups: dict[str, Callable] = {}


def register_lookup(label: str, lookup_function: Callable) -> None:
    """Register the lookup for the model ``label`` (``"cms.placeholder"``); replaces any earlier one."""
    _lookups[label.lower()] = lookup_function


def get_lookup(label: str) -> Callable:
    """The lookup for ``label``. Raises ``LookupError`` if none is registered."""
    try:
        return _lookups[label.lower()]
    except KeyError:
        raise LookupError(f"No lookup is registered for {label!r}.") from None


def lookup(label: str, pk: Any, context, *, admin: bool = False) -> Any:
    """The object of model ``label`` with primary key ``pk``, if ``context.user`` may see it.

    ``admin=True`` reads as an editor, drafts included; see the module documentation.

    :raises ~django.core.exceptions.ObjectDoesNotExist: if there is none, or the user may not see it.
    :raises LookupError: if no lookup is registered for ``label``.
    """
    return get_lookup(label)(pk, context, admin=admin)


def lookup_many(label: str, pks: Iterable[Any], context, *, admin: bool = False) -> list:
    """:func:`lookup` for each of ``pks``, in order; fails on the first that is not found."""
    function = get_lookup(label)
    return [function(pk, context, admin=admin) for pk in pks]
