"""Operation checks: one answer to "may this operation happen?".

Every service runs the checks registered for its operation before it changes
anything, and :func:`can` runs the same checks without changing anything -- a
dry run for the admin UI, an API or an assistant asking "can I ...?".

A check is a callable ``check(context, **target)`` that raises Django's own
``PermissionDenied`` or ``ValidationError`` and returns nothing when the
operation may proceed. ``context`` is the :class:`~cms.shared.operations.OperationContext`,
``target`` the service's arguments (``page=``, ``target_page=``, ...). Checks
should accept ``**kwargs`` so that a service can pass more later.

Checks are registered per operation (the names in :mod:`cms.operations`) under a
unique name. Core checks come first, in the order the core registers them; checks
from apps follow in ``INSTALLED_APPS`` order. An app replaces a core check by
registering one under the same name, in place::

    class MyCMSConfig(CMSAppConfig):
        cms_checks = {
            operations.MOVE_PAGE: [("myapp.page_unlocked", page_unlocked)],
        }

**Permission checks run first.** A real run stops at the first failure. A dry run
collects every validation failure, but stops at a permission failure so that the
reasons never tell a user more about content they may not touch.

These are unrelated to Django's system check framework (``manage.py check``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from importlib import import_module

from django.core.exceptions import PermissionDenied, ValidationError

__all__ = [
    "Reason",
    "Verdict",
    "can",
    "get_checks",
    "register_check",
    "run_checks",
]

#: Modules registering the core checks, imported on first use so that the
#: registry is complete however the caller reached it.
CORE_CHECK_MODULES = ("cms.pages.checks",)


@dataclass(frozen=True)
class _Entry:
    name: str
    check: Callable
    requires: tuple[str, ...]


# operation -> name -> entry. Dicts keep insertion order, which is check order.
_core: dict[str, dict[str, _Entry]] = {}
_extensions: dict[str, dict[str, _Entry]] = {}
_core_loaded = False


def _register(registry, operation, name, check, requires):
    registry.setdefault(operation, {})[name] = _Entry(name, check, tuple(requires))


def register_core_check(operation: str, name: str, check: Callable, *, requires: Iterable[str] = ()) -> None:
    """Register a django CMS core check. Apps use :func:`register_check`."""
    _register(_core, operation, name, check, requires)


def register_check(operation: str, name: str, check: Callable, *, requires: Iterable[str] = ()) -> None:
    """Add a check to ``operation``, or replace the check registered as ``name``.

    ``requires`` names the target arguments the check cannot do without. A dry
    run that lacks one of them skips the check and reports the verdict as
    incomplete, instead of guessing.
    """
    _register(_extensions, operation, name, check, requires)


def _load_core_checks():
    global _core_loaded
    if not _core_loaded:
        _core_loaded = True
        for module in CORE_CHECK_MODULES:
            import_module(module)


def get_checks(operation: str) -> list[_Entry]:
    """The checks for ``operation``, in the order they run."""
    _load_core_checks()
    extensions = dict(_extensions.get(operation, {}))
    entries = [extensions.pop(name, entry) for name, entry in _core.get(operation, {}).items()]
    return entries + list(extensions.values())


def run_checks(operation: str, context, **target) -> None:
    """Raise the first failure of ``operation``'s checks. Services call this."""
    for entry in get_checks(operation):
        missing = [arg for arg in entry.requires if arg not in target]
        if missing:
            raise TypeError(f"Check {entry.name!r} needs {', '.join(missing)} to run.")
        entry.check(context, **target)


@dataclass(frozen=True)
class Reason:
    """Why a check failed: the check's ``name``, its ``kind`` and the user-facing ``message``."""

    name: str
    kind: str  # "permission" or "validation"
    message: str


@dataclass(frozen=True)
class Verdict:
    """The outcome of a dry run. Truthy if the operation may proceed."""

    allowed: bool
    reasons: list[Reason] = field(default_factory=list)
    #: Names of checks skipped for want of a target argument. A verdict that
    #: skipped checks is not a promise: the real operation may still fail.
    skipped: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.skipped

    def __bool__(self) -> bool:
        return self.allowed

    def __str__(self) -> str:
        return " ".join(reason.message for reason in self.reasons)


def can(operation: str, context, **target) -> Verdict:
    """Dry-run ``operation``: run its checks, change nothing, report why not."""
    reasons = []
    skipped = []
    for entry in get_checks(operation):
        if any(arg not in target for arg in entry.requires):
            skipped.append(entry.name)
            continue
        try:
            entry.check(context, **target)
        except PermissionDenied as error:
            reasons.append(Reason(entry.name, "permission", str(error)))
            break
        except ValidationError as error:
            reasons.extend(Reason(entry.name, "validation", str(message)) for message in error.messages)
    return Verdict(allowed=not reasons, reasons=reasons, skipped=skipped)
