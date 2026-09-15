"""Late-bound lookups: one container asks a question, another answers it.

A signal (:mod:`cms.shared.signals`) fits when something *happened* and any
number of listeners may react. A resolver fits when the caller needs one answer
back -- a property getter cannot wait for a signal -- and the container that can
compute it is one the caller must not import.

The provider registers at import time; the caller resolves at call time, so the
lookup works regardless of which module loads first, and returns ``default``
when nobody provides it. That last part matters: a container must keep working
when the container that would answer is not installed.
"""

from collections.abc import Callable

__all__ = ["provide", "resolve", "providers"]

_resolvers: dict[str, Callable] = {}


def provide(name: str, func: Callable) -> Callable:
    """Register ``func`` as the implementation of ``name``.

    Replaces any previous implementation, so a project may override a built-in
    lookup. Returns ``func``, so this also works as a decorator.
    """
    _resolvers[name] = func
    return func


def resolve(name: str, *args, default=None, **kwargs):
    """Call the implementation of ``name``, or return ``default`` if unprovided."""
    func = _resolvers.get(name)
    if func is None:
        return default
    return func(*args, **kwargs)


def providers() -> dict[str, Callable]:
    """Every registered lookup, for introspection and tests."""
    return dict(_resolvers)
