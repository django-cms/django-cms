"""Operation checks: one answer to "may this operation happen?".

Every service runs the checks registered for its operation before it changes
anything, and :func:`can` runs the same checks without changing anything -- a
dry run for the admin UI, an API or an assistant asking "can I ...?".

A check is a callable ``check(context, **target)`` that raises
``PermissionDenied``, :class:`OperationBlocked` or ``ValidationError`` and returns
nothing when the operation may proceed. ``context`` is the :class:`~cms.shared.operations.OperationContext`,
``target`` the service's arguments (``page=``, ``target_page=``, ...). Checks
should accept ``**kwargs`` so that a service can pass more later.

Checks are registered per operation (the names in :mod:`cms.operations`) under a
unique name. They run by kind -- permission, then policy, then validation -- and
within a kind core checks come first, in the order the core registers them;
checks from apps follow in ``INSTALLED_APPS`` order. An app replaces a core check
by registering one under the same name, in place::

    class MyCMSConfig(CMSAppConfig):
        cms_checks = {
            operations.MOVE_PAGE: [("myapp.page_unlocked", page_unlocked)],
        }

**Permission checks run first.** A real run stops at the first failure. A dry run
collects every policy and validation failure, but stops at a permission failure
so that the reasons never tell a user more about content they may not touch.

Every check has a *kind*: :data:`PERMISSION` checks ask whether the acting user
may do this, :data:`POLICY` checks whether the object's state allows it right
now, whoever acts, and :data:`VALIDATION` checks whether the result would be
valid at all. Code acting on the system's own behalf -- :mod:`cms.api`,
management commands -- runs with ``OperationContext.system()``, which skips the
permission checks, runs the policy checks unless it opts out, and never skips
the validation checks.

These are unrelated to Django's system check framework (``manage.py check``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from django.core.exceptions import PermissionDenied, ValidationError

from cms.operations import get_operations

__all__ = [
    "PERMISSION",
    "POLICY",
    "VALIDATION",
    "OperationBlocked",
    "argument_problems",
    "Reason",
    "Verdict",
    "can",
    "get_checks",
    "register_check",
    "run_checks",
]

#: Check kinds, in the order they run. A *permission* check asks whether the
#: acting user may perform the operation; a system context
#: (``OperationContext.system()``) skips it. A *policy* check asks whether the
#: object's state allows the operation right now, whoever acts -- published
#: content is read-only, a draft is locked by another user; a system context runs
#: it unless created with ``policy=False``. A *validation* check asks whether the
#: result would be valid at all, and always runs.
PERMISSION = "permission"
POLICY = "policy"
VALIDATION = "validation"
KINDS = (PERMISSION, POLICY, VALIDATION)


class OperationBlocked(PermissionDenied):
    """The object's state does not allow the operation right now, whoever acts.

    Raised by policy checks. A subclass of ``PermissionDenied`` so that code
    handling that keeps refusing; the admin answers it with 409 instead of 403.
    """


@dataclass(frozen=True)
class _Entry:
    name: str
    check: Callable
    requires: tuple[str, ...]
    kind: str


# operation -> name -> entry. Dicts keep insertion order, which is check order.
_core: dict[str, dict[str, _Entry]] = {}
_extensions: dict[str, dict[str, _Entry]] = {}


def _register(registry, operation, name, check, requires, kind):
    if kind not in KINDS:
        raise ValueError(f"Check {name!r} has kind {kind!r}; expected one of {', '.join(KINDS)}.")
    registry.setdefault(operation, {})[name] = _Entry(name, check, tuple(requires), kind)


def register_core_check(
    operation: str, name: str, check: Callable, *, kind: str, requires: Iterable[str] = ()
) -> None:
    """Register a django CMS core check. Apps use :func:`register_check`.

    Core checks are kept apart from the apps' checks, so that an app can replace
    one by name whichever of the two registers first. Their ``kind`` is required:
    whether a system context skips a core check must never be left to a default.
    """
    _register(_core, operation, name, check, requires, kind)


def register_check(
    operation: str, name: str, check: Callable, *, requires: Iterable[str] = (), kind: str = VALIDATION
) -> None:
    """Add a check to ``operation``, or replace the check registered as ``name``.

    ``requires`` names the target arguments the check cannot do without. A dry
    run that lacks one of them skips the check and reports the verdict as
    incomplete, instead of guessing.

    ``kind`` is :data:`PERMISSION` for a check about the acting user, which a
    system context skips, :data:`POLICY` for a check about the object's state,
    or :data:`VALIDATION` (the default) for a check that the result must pass
    whoever acts.
    """
    _register(_extensions, operation, name, check, requires, kind)


def _applies(entry, context) -> bool:
    if entry.kind == PERMISSION:
        return not getattr(context, "is_system", False)
    if entry.kind == POLICY:
        return getattr(context, "policy", True)
    return True


def get_checks(operation: str) -> list[_Entry]:
    """The checks for ``operation``, in the order they run.

    By kind -- permission, policy, validation -- and within a kind core checks
    first, then the apps' checks. An app check replacing a core check by name
    takes its place.
    """
    extensions = dict(_extensions.get(operation, {}))
    entries = [extensions.pop(name, entry) for name, entry in _core.get(operation, {}).items()]
    entries += extensions.values()
    return sorted(entries, key=lambda entry: KINDS.index(entry.kind))


def argument_problems() -> list[str]:
    """Checks that require an argument their operation does not declare.

    An adapter -- REST, MCP -- calls :func:`can` with the operation's declared
    arguments. A check requiring any other name is skipped in that dry run
    (:attr:`Verdict.skipped`), so the dry run approves what the service may
    refuse. Operations without declared arguments are not checked. ``manage.py
    cms check`` reports these.
    """
    problems = []
    for declaration in get_operations():
        if declaration.arguments is None:
            continue
        declared = {argument.name for argument in declaration.arguments}
        for entry in get_checks(declaration.id):
            problems.extend(
                f"Check {entry.name!r} of operation {declaration.id!r} requires {name!r}, "
                f"which the operation does not declare."
                for name in entry.requires
                if name not in declared
            )
    return problems


def run_checks(operation: str, context, **target) -> None:
    """Raise the first failure of ``operation``'s checks. Services call this."""
    for entry in get_checks(operation):
        if not _applies(entry, context):
            continue
        missing = [arg for arg in entry.requires if arg not in target]
        if missing:
            raise TypeError(f"Check {entry.name!r} needs {', '.join(missing)} to run.")
        entry.check(context, **target)


@dataclass(frozen=True)
class Reason:
    """Why a check failed: the check's ``name``, its ``kind`` and the user-facing ``message``.

    ``kind`` follows the exception the check raised: ``"permission"`` for
    ``PermissionDenied``, ``"policy"`` for :class:`OperationBlocked`,
    ``"validation"`` for ``ValidationError``.
    """

    name: str
    kind: str  # "permission", "policy" or "validation"
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
        if not _applies(entry, context):
            continue
        if any(arg not in target for arg in entry.requires):
            skipped.append(entry.name)
            continue
        try:
            entry.check(context, **target)
        except OperationBlocked as error:
            reasons.append(Reason(entry.name, POLICY, str(error)))
        except PermissionDenied as error:
            reasons.append(Reason(entry.name, PERMISSION, str(error)))
            break
        except ValidationError as error:
            reasons.extend(Reason(entry.name, VALIDATION, str(message)) for message in error.messages)
    return Verdict(allowed=not reasons, reasons=reasons, skipped=skipped)
