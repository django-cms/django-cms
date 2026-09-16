"""Compatibility shims for names that changed location.

Every class or function that moves keeps a re-export at its original dotted
path (rule R1 of the django CMS 6 refactor), and every such shim is declared
here rather than hand-written (rule R2), so that the complete set stays
machine-enumerable and deprecation warnings can be switched on later without
touching a single call site.

A shim module looks like this::

    # cms/models/pagemodel.py
    from cms.compat import moved

    __getattr__, __dir__, __all__ = moved(__name__, {
        "Page": "cms.pages.models.page.Page",
        "PageUrl": "cms.pages.models.page.PageUrl",
    }, since="6.0")

``__all__`` matters: :pep:`562` module ``__getattr__`` is not consulted by
``from ... import *``, and several CMS modules are star-imported (notably into
``cms.models``). Returning the three names together makes that impossible to
forget.

The shim resolves to the moved object itself, never a copy or a subclass, so
``isinstance`` checks, ``issubclass`` checks and ``sender=Page`` signal wiring
keep working across both paths.

Passing ``warn=`` turns an entry into a deprecation. django CMS 6.0 ships with
``warn=None`` throughout: the release that performs a move has to be silent
about it, because downstream code cannot yet import the new location from any
released version.
"""

import importlib
from typing import NamedTuple

__all__ = ["MovedName", "moved", "registry", "resolve"]


class MovedName(NamedTuple):
    """One relocated name, as recorded by :func:`moved`."""

    #: Dotted path the name used to live at, e.g. ``cms.models.pagemodel.Page``.
    old_path: str
    #: Dotted path it lives at now.
    new_path: str
    #: django CMS version that performed the move, e.g. ``"6.0"``.
    since: str
    #: Warning category to raise on access, or ``None`` while the shim is silent.
    warn: type[Warning] | None


_registry: dict[str, MovedName] = {}


def resolve(path: str):
    """Import and return the object at a dotted ``path``."""
    module_path, _, attribute = path.rpartition(".")
    if not module_path:
        raise ValueError(f"{path!r} is not a dotted path to an object")
    return getattr(importlib.import_module(module_path), attribute)


def moved(
    module: str,
    names: dict[str, str],
    *,
    since: str,
    warn: type[Warning] | None = None,
    fallback: str | None = None,
):
    """Declare that ``names`` used to live in ``module`` and record the move.

    :param module: the shim module's own ``__name__``.
    :param names: maps each old attribute name to its new dotted path.
    :param since: django CMS version that performed the move.
    :param warn: warning category to raise on access, or ``None`` to stay silent.
    :param fallback: for a module moved wholesale, the module it moved to. Any
        name not in ``names`` is then looked up there.

        This matters more than it looks. A module's namespace holds everything it
        imported, not only what it defined, and callers do reach for those --
        ``cms.admin.forms.ValidationError`` was a real example found by the test
        suite. A shim built only from declared names silently narrows the
        namespace and breaks them. Pointing at the new module preserves the old
        behaviour exactly, accidental leakage included.
    :returns: ``(__getattr__, __dir__, __all__)`` for the shim module to bind.
    """
    for old_name, new_path in names.items():
        old_path = f"{module}.{old_name}"
        previous = _registry.get(old_path)
        if previous is not None and previous.new_path != new_path:
            raise RuntimeError(
                f"{old_path} is already declared as moved to {previous.new_path}, "
                f"cannot also declare it moved to {new_path}"
            )
        _registry[old_path] = MovedName(old_path, new_path, since, warn)

    def __getattr__(name: str):
        entry = _registry.get(f"{module}.{name}")
        if entry is None:
            if fallback and not name.startswith("__"):
                try:
                    return resolve(f"{fallback}.{name}")
                except AttributeError:
                    pass
            raise AttributeError(f"module {module!r} has no attribute {name!r}")
        if entry.warn is not None:
            # Raised lazily, so a module that is merely imported stays quiet and
            # only actual use of a moved name is reported.
            import warnings

            warnings.warn(
                f"{entry.old_path} moved to {entry.new_path} in django CMS {entry.since}. "
                f"Import it from its new location.",
                entry.warn,
                stacklevel=2,
            )
        return resolve(entry.new_path)

    def __dir__():
        return sorted(names)

    # Private names are shimmed but kept out of ``__all__``, so a star-import of
    # the shim exports exactly what a star-import of the original module did.
    return __getattr__, __dir__, sorted(name for name in names if not name.startswith("_"))


def registry() -> tuple[MovedName, ...]:
    """Every declared move, ordered by old path.

    This is the deprecation schedule: what moved, where to, when, and whether it
    warns yet. Only entries whose shim module has been imported are present, so
    callers that need the full picture (release notes, docs cross-references,
    the shim test) must import the CMS app tree first.
    """
    return tuple(sorted(_registry.values()))
