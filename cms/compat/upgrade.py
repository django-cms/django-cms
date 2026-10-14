"""``cmsupgrade``: rewrite imports of moved django CMS names to their new paths.

Every name that moved in django CMS 6 keeps a shim at its old path, declared
with :func:`cms.compat.moved`. This tool reads those declarations and rewrites
Python sources so they import from the new locations directly, in the spirit of
``pyupgrade`` and ``django-upgrade``::

    cmsupgrade src/ another_app/models.py

Directories are searched recursively for ``*.py`` files. Files are rewritten in
place; ``--diff`` shows the changes instead and ``--check`` only reports which
files would change. The exit status is 1 if any file was (or would be) changed.

What gets rewritten:

* ``from cms.plugin_base import CMSPluginBase`` becomes
  ``from cms.core.plugin_base import CMSPluginBase``. Imports whose names moved
  to different modules are split, and names that did not move stay where they
  are.
* ``from cms import plugin_pool`` and ``import cms.plugin_pool as pool`` follow a
  module that moved wholesale. A plain ``import cms.plugin_pool`` is rewritten
  together with every ``cms.plugin_pool`` reference in the file.
* ``import cms.toolbar.utils`` (with or without ``as``) and ``from cms.toolbar
  import utils`` of a module that moved in part: each reference to a moved name
  is rewritten to its new path and the new module imported. This is the form
  migrations use, so migrations are covered too. The same applies to names that
  did not follow their module's move (``cms.admin.forms`` moved to pages, but
  ``RequestToolbarForm`` to core). A module whose names went to different
  places and that is used as an object (``handler(forms)``) is reported and
  left alone.
* String literals holding a dotted path to a moved name, typically
  ``mock.patch("cms.plugin_pool.plugin_pool")`` targets. Disable with
  ``--no-strings``.

Star imports from a moved module are reported but left alone.

The move table is read statically from the installed django CMS source, so no
Django settings are needed. Only use the result in code that no longer needs to
support django CMS 5.x: the new paths do not exist there. Rewritten imports may
be out of order; run ``isort`` or ``ruff`` afterwards.
"""

import argparse
import ast
import difflib
import io
import re
import sys
import tokenize
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from cms.compat._scopes import Scope, Scopes

__all__ = ["MoveTable", "load_move_table", "main", "rewrite_source"]

#: Packages whose ``moved()`` declarations make up the move table.
PACKAGES = ("cms", "menus")
#: Subpackages that declare moves for test purposes only.
SKIP_PACKAGES = ("cms.tests",)
#: Directory names never descended into when searching for sources.
SKIP_DIRS = frozenset(
    {".git", ".hg", ".svn", ".tox", ".nox", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}
)
#: Upper bound when following a name that moved more than once.
MAX_HOPS = 10


@dataclass
class MoveTable:
    """Where moved names and modules live now."""

    #: Old dotted path of a name -> new dotted path.
    names: dict[str, str] = field(default_factory=dict)
    #: Old module moved wholesale -> the module it moved to (``fallback=``).
    modules: dict[str, str] = field(default_factory=dict)
    #: Names a shim module still defines or imports itself; never rewritten.
    defined: dict[str, frozenset[str]] = field(default_factory=dict)

    def shim_modules(self) -> set[str]:
        return {path.rpartition(".")[0] for path in self.names} | set(self.modules)

    def lookup(self, module: str, name: str) -> str | None:
        """New dotted path of ``module.name``, or ``None`` if it did not move."""
        start = path = f"{module}.{name}"
        for _ in range(MAX_HOPS):
            if path in self.names:
                new = self.names[path]
            else:
                module, _, name = path.rpartition(".")
                if module in self.modules and name not in self.defined.get(module, ()) and not name.startswith("__"):
                    new = f"{self.modules[module]}.{name}"
                else:
                    break
            if new == path:
                break
            path = new
        return None if path == start else path

    def has_exceptions(self, module: str) -> bool:
        """Whether some of ``module``'s names did not move to its ``fallback``."""
        target = self.module_target(module)
        prefix = f"{module}."
        for old_path in self.names:
            if old_path.startswith(prefix) and "." not in old_path[len(prefix) :]:
                new_path = self.lookup(module, old_path[len(prefix) :])
                if new_path is None or new_path.rpartition(".")[0] != target:
                    return True
        return False

    def module_target(self, module: str) -> str | None:
        """New path of a module that moved wholesale, or ``None``."""
        if module not in self.modules:
            return None
        for _ in range(MAX_HOPS):
            if module not in self.modules:
                break
            module = self.modules[module]
        return module


# --------------------------------------------------------------------------
# Reading the move table from the installed sources
# --------------------------------------------------------------------------


def _package_roots() -> Iterator[tuple[str, Path]]:
    import importlib.util

    for package in PACKAGES:
        spec = importlib.util.find_spec(package)
        if spec is None or not spec.submodule_search_locations:
            continue
        for location in spec.submodule_search_locations:
            yield package, Path(location)


def _module_name(package: str, root: Path, path: Path) -> str:
    parts = [package, *path.relative_to(root).with_suffix("").parts]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _top_level_names(tree: ast.Module) -> set[str]:
    """Names a module binds itself, excluding what ``moved()`` returns."""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.partition(".")[0])
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return names - {"__getattr__", "__dir__", "__all__", "moved"}


def _read_declarations(table: MoveTable, module: str, tree: ast.Module) -> None:
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            (isinstance(func, ast.Name) and func.id == "moved")
            or (isinstance(func, ast.Attribute) and func.attr == "moved")
        ):
            continue
        if len(node.args) < 2 or not isinstance(node.args[1], ast.Dict):
            continue
        first = node.args[0]
        old_module = module if isinstance(first, ast.Name) and first.id == "__name__" else _string(first)
        if old_module is None:
            continue
        found = True
        for key, value in zip(node.args[1].keys, node.args[1].values, strict=True):
            old_name, new_path = _string(key), _string(value)
            if old_name and new_path:
                table.names[f"{old_module}.{old_name}"] = new_path
        for keyword in node.keywords:
            if keyword.arg == "fallback" and _string(keyword.value):
                table.modules[old_module] = _string(keyword.value)
    if found:
        table.defined[module] = frozenset(_top_level_names(tree))


def load_move_table() -> MoveTable:
    """Collect every ``moved()`` declaration of the installed django CMS."""
    table = MoveTable()
    for package, root in _package_roots():
        for path in sorted(root.rglob("*.py")):
            module = _module_name(package, root, path)
            if module.startswith(SKIP_PACKAGES):
                continue
            try:
                source = path.read_bytes()
            except OSError:
                continue
            if b"moved" not in source:
                continue
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                continue
            _read_declarations(table, module, tree)
    return table


# --------------------------------------------------------------------------
# Rewriting a source file
# --------------------------------------------------------------------------


@dataclass
class Result:
    source: str
    warnings: list[tuple[int, str]] = field(default_factory=list)


class _Offsets:
    """Convert ``ast`` positions (line, UTF-8 byte column) to string offsets."""

    def __init__(self, source: str):
        self.source = source
        self.starts = [0]
        for match in re.finditer(r"\r\n|\r|\n", source):
            self.starts.append(match.end())

    def __call__(self, lineno: int, col: int) -> int:
        start = self.starts[lineno - 1]
        end = self.starts[lineno] if lineno < len(self.starts) else len(self.source)
        line = self.source[start:end].encode("utf-8")
        return start + len(line[:col].decode("utf-8"))

    def span(self, node: ast.AST) -> tuple[int, int]:
        return self(node.lineno, node.col_offset), self(node.end_lineno, node.end_col_offset)

    def line_prefix(self, offset: int) -> str:
        start = self.source.rfind("\n", 0, offset) + 1
        return self.source[start:offset]


def _dotted(node: ast.AST) -> str | None:
    """``a.b.c`` for an attribute chain rooted in a plain name."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def _format_alias(name: str, asname: str | None) -> str:
    return f"{name} as {asname}" if asname and asname != name else name


def _format_from(module: str, aliases: list[tuple[str, str]], multiline: bool, indent: str) -> str:
    if multiline:
        body = "".join(f"{indent}    {alias},{'  ' + comment if comment else ''}\n" for alias, comment in aliases)
        return f"from {module} import (\n{body}{indent})"
    return f"from {module} import {', '.join(alias for alias, _ in aliases)}"


def _alias_comments(node: ast.ImportFrom, statement: str) -> tuple[dict[int, str], int]:
    """Trailing comments of a parenthesised import, keyed by alias index.

    Returns the comments that could be attached to the last name on their line,
    and how many could not (for example one on the line of the opening paren).
    """
    comments = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(statement).readline):
            if token.type == tokenize.COMMENT:
                comments[node.lineno + token.start[0] - 1] = token.string
    except (tokenize.TokenError, SyntaxError):
        return {}, len(comments)
    attached = {}
    for index, alias in enumerate(node.names):
        is_last_on_line = index + 1 == len(node.names) or node.names[index + 1].lineno != alias.end_lineno
        if is_last_on_line and alias.end_lineno in comments:
            attached[index] = comments.pop(alias.end_lineno)
    return attached, len(comments)


_FROM_MODULE = re.compile(r"from\s+((?:\w+\s*\.\s*)*\w+)")
_SIMPLE_STRING = re.compile(r"""\A([rRuU]?)('''|\"\"\"|'|")(.*)\2\Z""", re.DOTALL)


@dataclass
class _Binding:
    """A local name bound to a moved module by an import statement."""

    #: The module as imported, e.g. ``cms.admin.forms``.
    module: str
    #: How the code refers to it: ``cms.admin.forms``, an ``as`` name, or ``forms``.
    ref: str
    #: The module the binding now points at -- the shim's ``fallback`` -- or
    #: ``None`` if the module did not move wholesale and the import stays.
    target: str | None
    #: ``import a.b`` without ``as``: references spell out the dotted path.
    plain: bool
    #: Modules that must be imported because references now name them.
    extra: list[str] = field(default_factory=list)
    #: The binding is still referenced and its import must stay.
    still_used: bool = False
    #: The scope the import binds in.
    scope: Scope | None = None
    #: Line of the first import making the binding, for warnings.
    lineno: int = 0
    #: The scopes the binding's import statements are in; imports it needs are
    #: added next to them.
    statement_scopes: list[Scope] = field(default_factory=list)
    #: The name is bound in other ways too (a parameter, an assignment, another
    #: module): which references mean the module cannot be told, so none move.
    ambiguous: bool = False

    @property
    def dropped(self) -> bool:
        """Every reference was rewritten to another module; the import can go."""
        return not self.still_used and bool(self.extra)


@dataclass
class _Alias:
    """One name of an import statement, after rewriting."""

    #: The module imported from (``from`` imports) or imported (plain imports).
    module: str
    #: The imported name; ``None`` for plain imports.
    name: str | None
    local: str | None
    binding: _Binding | None = None

    # A binding follows its target, which is only settled once the references
    # have been analysed; until then the alias keeps the original path.
    @property
    def final_module(self) -> str:
        if self.binding and self.binding.target:
            return self.binding.target if self.name is None else self.binding.target.rpartition(".")[0]
        return self.module

    @property
    def final_name(self) -> str | None:
        if self.binding and self.binding.target and self.name is not None:
            return self.binding.target.rpartition(".")[2]
        return self.name

    @property
    def kept(self) -> bool:
        return not (self.binding and self.binding.dropped)


def _plan_import_from(node, table, shims, warnings, get_binding) -> list[_Alias] | None:
    if node.level or not node.module:
        return None
    module = node.module
    if any(alias.name == "*" for alias in node.names):
        if module in shims:
            warnings.append((node.lineno, f"star import from moved module {module}; update it manually"))
        return None
    plan = []
    for alias in node.names:
        local = alias.asname or alias.name
        new_path = table.lookup(module, alias.name)
        if new_path is not None:
            new_module, _, new_name = new_path.rpartition(".")
            plan.append(_Alias(new_module, new_name, local))
            continue
        imported_module = f"{module}.{alias.name}"
        if imported_module in shims:
            # ``from cms.admin import forms``: the name is a moved module.
            binding = get_binding(node, imported_module, local, plain=False)
            plan.append(_Alias(module, alias.name, local, binding))
            continue
        plan.append(_Alias(module, alias.name, local))
    return plan


def _plan_import(node, shims, get_binding) -> list[_Alias] | None:
    plan = []
    relevant = False
    for alias in node.names:
        if alias.name not in shims:
            plan.append(_Alias(alias.name, None, alias.asname))
            continue
        relevant = True
        binding = get_binding(node, alias.name, alias.asname or alias.name, plain=alias.asname is None)
        plan.append(_Alias(alias.name, None, alias.asname, binding))
    return plan if relevant else None


def _bound_module(statement, local: str) -> str | None:
    """The module ``statement`` binds to the name ``local``, if it binds a module to it."""
    for alias in statement.names:
        if isinstance(statement, ast.Import):
            if alias.asname == local:
                return alias.name
        elif (alias.asname or alias.name) == local and statement.module and not statement.level:
            return f"{statement.module}.{alias.name}"
    return None


def _binds_root(statement, root: str) -> bool:
    """Whether ``statement`` is a plain ``import root.x`` (binding ``root`` to the package)."""
    return isinstance(statement, ast.Import) and any(
        alias.asname is None and alias.name.partition(".")[0] == root for alias in statement.names
    )


def _check_ambiguity(binding: _Binding) -> None:
    hows = binding.scope.bindings.get(binding.ref.partition(".")[0] if binding.plain else binding.ref, [])
    if binding.plain:
        root = binding.ref.partition(".")[0]
        clear = all(how is not None and _binds_root(how, root) for how in hows)
    else:
        clear = all(how is not None and _bound_module(how, binding.ref) == binding.module for how in hows)
    binding.ambiguous = binding.scope.star or not clear


def _bindings_of(bindings_by_key, scope: Scope, name: str):
    """The bindings in ``scope`` a reference spelled with ``name`` may read."""
    for (scope_id, ref), binding in bindings_by_key.items():
        if scope_id == id(scope) and (ref == name or (binding.plain and ref.partition(".")[0] == name)):
            yield binding


def _find_references(tree, scopes, bindings_by_key) -> dict[int, list[tuple[ast.AST, Scope]]]:
    """The nodes that read each binding: ``id(binding)`` -> module expression nodes and their scopes.

    For ``import cms.toolbar.utils`` that is each ``cms.toolbar.utils`` attribute
    whose ``cms`` resolves to the import's scope; for an ``as`` or ``from`` import
    each ``utils`` name that does.
    """
    parent_attribute = {id(node.value): node for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    references: dict[int, list[tuple[ast.AST, Scope]]] = {}
    for name, scope in scopes.loads:
        if scope.reads_uncertain(name.id):
            # Which binding this reads depends on statement order: none of the
            # candidates can be rewritten safely.
            for candidate_scope in scope.read_candidates(name.id):
                for binding in _bindings_of(bindings_by_key, candidate_scope, name.id):
                    binding.ambiguous = True
            continue
        resolved = scope.resolve(name.id)
        if resolved is None:
            continue
        binding = bindings_by_key.get((id(resolved), name.id))
        value = name if binding is not None and not binding.plain else None
        if value is None:
            # ``cms.toolbar.utils``: the longest imported module the chain spells.
            binding = None
            node, dotted = name, name.id
            while id(node) in parent_attribute:
                node = parent_attribute[id(node)]
                dotted = f"{dotted}.{node.attr}"
                candidate = bindings_by_key.get((id(resolved), dotted))
                if candidate is not None and candidate.plain:
                    binding, value = candidate, node
        if binding is not None:
            references.setdefault(id(binding), []).append((value, scope))
    return references


def _rewrite_references(tree, scopes, table, offsets, edits, warnings, bindings_by_key):
    """Follow each moved-module binding into the references made through it.

    The binding itself points at the module's ``fallback`` if it has one. A name
    that moved somewhere else -- an exception to the fallback, like
    ``RequestToolbarForm`` in ``cms.admin.forms`` -- is rewritten to its full new
    path, and that module is imported next to the binding.
    """
    if not bindings_by_key:
        return
    parent_attribute = {id(node.value): node for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    references = _find_references(tree, scopes, bindings_by_key)
    # ``nonlocal utils`` needs ``utils`` bound in the enclosing function: the
    # import stays even if no reference is left.
    declared_nonlocal = {
        (id(target), name)
        for scope, name in scopes.nonlocal_declarations
        if (target := scope.outer_binding(name)) is not None
    }

    def leave_alone(binding, lineno, reason):
        # The import stays as it is: it keeps working through the shim.
        binding.target = None
        binding.still_used = True
        warnings.append((lineno, f"{reason}; update its uses of {binding.module} manually"))

    for binding in bindings_by_key.values():
        if binding.ambiguous:
            leave_alone(binding, binding.lineno, f"{binding.ref} may also refer to something else")
            continue
        values = references.get(id(binding), [])
        bare = [value for value, _ in values if id(value) not in parent_attribute]
        if bare and binding.target and table.has_exceptions(binding.module):
            # The module object itself is passed around, so the names that moved
            # elsewhere may be read from it anywhere. The fallback lacks them.
            leave_alone(
                binding,
                bare[0].lineno,
                f"{binding.ref} is used as a module, and not all names of {binding.module} moved to the same place",
            )
            continue
        planned = []
        extra = []
        # Scopes the references rewritten to a full new path are read in.
        reading_scopes = []
        for value, reading_scope in values:
            node = parent_attribute.get(id(value))
            if node is None:
                # The module itself is used, not one of its names.
                binding.still_used = True
                if binding.target and binding.plain:
                    planned.append((*offsets.span(value), binding.target))
                continue
            new_path = table.lookup(binding.module, node.attr)
            if new_path is None:
                binding.still_used = True
                continue
            new_module, _, new_name = new_path.rpartition(".")
            if binding.target and new_module == binding.target and new_name == node.attr:
                binding.still_used = True
                if binding.plain:
                    planned.append((*offsets.span(value), binding.target))
                continue
            planned.append((*offsets.span(node), new_path))
            reading_scopes.append(reading_scope)
            if new_module not in extra:
                extra.append(new_module)
        problem = _check_new_imports(scopes, binding, extra, reading_scopes)
        if problem:
            leave_alone(binding, binding.lineno, problem)
            continue
        binding.extra = extra
        if (id(binding.scope), binding.ref.partition(".")[0] if binding.plain else binding.ref) in declared_nonlocal:
            binding.still_used = True
        edits.extend(planned)


#: Stands for an import ``cmsupgrade`` is about to add, while checking it.
_ADDED = object()


def _check_new_imports(scopes: Scopes, binding: _Binding, modules: list[str], reading_scopes: list[Scope]):
    """Why the imports for ``modules`` cannot be added next to ``binding``, or ``None``.

    Each import binds the package name (``cms``) in the scopes of the binding's
    import statements, and every rewritten reference must then read that package.
    """
    for root in dict.fromkeys(module.partition(".")[0] for module in modules):
        added = list(dict.fromkeys(scope.binding_scope(root) for scope in binding.statement_scopes))
        for scope in added:
            if not _can_import_here(scopes, scope, root):
                return f"importing the new location would rebind {root!r} next to {binding.ref}"
        for reading_scope in reading_scopes:
            if not _reads_package(reading_scope, root, added):
                return f"{root!r} means something else where {binding.ref} is used"
    return None


def _reads_package(reading_scope: Scope, root: str, added: list[Scope]) -> bool:
    """Whether ``root`` read in ``reading_scope`` is the package, once ``added`` import it."""
    if reading_scope.reads_uncertain(root):
        return False
    newly_bound = [scope for scope in added if root not in scope.bindings]
    for scope in newly_bound:
        scope.bindings[root] = [_ADDED]
    try:
        resolved = reading_scope.resolve(root)
        if resolved is None or resolved.star:
            return False
        hows = resolved.bindings.get(root, [])
        return bool(hows) and all(how is _ADDED or (how is not None and _binds_root(how, root)) for how in hows)
    finally:
        for scope in newly_bound:
            del scope.bindings[root]


def _can_import_here(scopes: Scopes, scope: Scope, root: str) -> bool:
    """Whether an ``import root.x`` can be added to ``scope`` without changing what code reads.

    That is harmless where ``root`` is only bound by such imports already.
    Anything else bound to it would be replaced, and in a function the name would
    become local, so a read of the outer ``root`` before the new import would fail.
    """
    hows = scope.bindings.get(root)
    if hows is not None:
        return all(how is not None and _binds_root(how, root) for how in hows) and not scope.star
    if scope.kind == "module":
        return not scope.star
    for name, reading_scope in scopes.loads:
        if name.id != root or not _is_within(reading_scope, scope):
            continue
        resolved = reading_scope.resolve(root)
        if resolved is None or not _is_within(resolved, scope):
            return False
    return True


def _is_within(scope: Scope, ancestor: Scope) -> bool:
    while scope is not None:
        if scope is ancestor:
            return True
        scope = scope.parent
    return False


def _statement_layout(node, offsets):
    start, end = offsets.span(node)
    prefix = offsets.line_prefix(start)
    indent = prefix if not prefix.strip() else ""
    separator = f"\n{indent}" if not prefix.strip() else "; "
    return start, end, indent, separator


def _extra_imports(plan) -> list[str]:
    extra = []
    for alias in plan:
        if alias.binding:
            extra += [module for module in alias.binding.extra if module not in extra]
    return extra


def _emit_import_from(node, plan, offsets, edits, warnings):
    kept = [alias for alias in plan if alias.kept]
    extra = _extra_imports(plan)
    unchanged = len(kept) == len(plan) and all(
        alias.final_module == node.module and alias.final_name == original.name
        for alias, original in zip(plan, node.names, strict=True)
    )
    if unchanged and not extra:
        return

    start, end, indent, separator = _statement_layout(node, offsets)
    statement = offsets.source[start:end]
    new_modules = {alias.final_module for alias in kept}
    names_kept = len(kept) == len(plan) and all(
        alias.final_name == original.name for alias, original in zip(plan, node.names, strict=True)
    )
    match = _FROM_MODULE.match(statement)
    if len(new_modules) == 1 and names_kept and match:
        # Only the module changed: swap it and keep the rest, comments included.
        edits.append((start + match.start(1), start + match.end(1), new_modules.pop()))
        if extra:
            edits.append((end, end, separator + separator.join(f"import {module}" for module in extra)))
        return

    multiline = "\n" in statement and "(" in statement
    comments, dropped = _alias_comments(node, statement) if multiline else ({}, 0)
    if dropped:
        warnings.append((node.lineno, f"comments inside the import from {node.module} were dropped"))
    groups: dict[str, list[tuple[str, str]]] = {}
    for index, alias in enumerate(plan):
        if alias.kept:
            groups.setdefault(alias.final_module, []).append(
                (_format_alias(alias.final_name, alias.local), comments.get(index, ""))
            )
    lines = [_format_from(module, aliases, multiline, indent) for module, aliases in groups.items()]
    lines += [f"import {module}" for module in extra]
    edits.append((start, end, separator.join(lines)))


def _emit_import(node, plan, offsets, edits):
    kept = [alias for alias in plan if alias.kept]
    extra = _extra_imports(plan)
    unchanged = len(kept) == len(plan) and all(
        alias.final_module == original.name for alias, original in zip(plan, node.names, strict=True)
    )
    if unchanged and not extra:
        return
    start, end, _, separator = _statement_layout(node, offsets)
    lines = []
    if kept:
        lines.append(f"import {', '.join(_format_alias(alias.final_module, alias.local) for alias in kept)}")
    lines += [f"import {module}" for module in extra]
    edits.append((start, end, separator.join(lines)))


def _rewrite_string(node, table, shims, offsets, edits):
    value = node.value
    if "." not in value or not value.isascii() or " " in value:
        return
    parts = value.split(".")
    for i in range(len(parts) - 1, 0, -1):
        module = ".".join(parts[:i])
        if module not in shims:
            continue
        new_path = table.lookup(module, parts[i])
        if new_path is None:
            return
        new_value = ".".join([new_path, *parts[i + 1 :]])
        start, end = offsets.span(node)
        match = _SIMPLE_STRING.match(offsets.source[start:end])
        if match and match.group(3) == value:
            quote = match.group(2)
            edits.append((start, end, f"{match.group(1)}{quote}{new_value}{quote}"))
        return


def rewrite_source(source: str, table: MoveTable, *, strings: bool = True, filename: str = "<string>") -> Result:
    """Rewrite moved imports in ``source``; raises ``SyntaxError`` if it does not parse."""
    tree = ast.parse(source, filename=filename)
    offsets = _Offsets(source)
    edits: list[tuple[int, int, str]] = []
    warnings: list[tuple[int, str]] = []
    shims = table.shim_modules()

    in_fstring = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            in_fstring.update(id(sub) for sub in ast.walk(node))

    scopes = Scopes(tree)
    # One binding per scope and name: the same module imported twice in a scope
    # is one binding, so each reference is rewritten exactly once.
    bindings_by_key: dict[tuple[int, str], _Binding] = {}

    def get_binding(statement, module, ref, plain):
        statement_scope = scopes.scope_of[id(statement)]
        # ``global forms`` in a function makes its import bind at module level.
        scope = statement_scope.binding_scope(ref.partition(".")[0] if plain else ref)
        key = (id(scope), ref)
        binding = bindings_by_key.get(key)
        if binding is None:
            binding = bindings_by_key[key] = _Binding(
                module, ref, table.module_target(module), plain, scope=scope, lineno=statement.lineno
            )
        if statement_scope not in binding.statement_scopes:
            binding.statement_scopes.append(statement_scope)
        return binding

    # Plan every import first: how a statement is rewritten depends on how the
    # modules it binds are used, which only the references can tell.
    statements = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            plan = _plan_import_from(node, table, shims, warnings, get_binding)
        elif isinstance(node, ast.Import):
            plan = _plan_import(node, shims, get_binding)
        else:
            if (
                strings
                and isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in in_fstring
            ):
                _rewrite_string(node, table, shims, offsets, edits)
            continue
        if plan:
            statements.append((node, plan))

    for binding in bindings_by_key.values():
        _check_ambiguity(binding)
    _rewrite_references(tree, scopes, table, offsets, edits, warnings, bindings_by_key)
    for node, plan in statements:
        if isinstance(node, ast.ImportFrom):
            _emit_import_from(node, plan, offsets, edits, warnings)
        else:
            _emit_import(node, plan, offsets, edits)

    for start, end, text in sorted(edits, reverse=True):
        source = source[:start] + text + source[end:]
    return Result(source, sorted(warnings))


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def _package_dirs() -> list[Path]:
    return [root.resolve() for _, root in _package_roots()]


def iter_python_files(paths: Iterable[str]) -> Iterator[Path]:
    """Python files below ``paths``, skipping VCS, virtualenv and build dirs."""
    excluded = _package_dirs()
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            yield path
            continue
        for candidate in sorted(path.rglob("*.py")):
            relative = candidate.relative_to(path).parts[:-1]
            if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in relative):
                continue
            if any((path.joinpath(*relative[: i + 1]) / "pyvenv.cfg").exists() for i in range(len(relative))):
                continue
            resolved = candidate.resolve()
            # The shims declare the old paths; rewriting them would break them.
            if any(resolved.is_relative_to(root) for root in excluded):
                continue
            yield candidate


def _process(path: Path, table: MoveTable, args) -> bool:
    raw = path.read_bytes()
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
        source = raw.decode(encoding)
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"{path}: skipped, cannot decode: {exc}", file=sys.stderr)
        return False
    try:
        result = rewrite_source(source, table, strings=args.strings, filename=str(path))
    except SyntaxError as exc:
        print(f"{path}:{exc.lineno}: skipped, syntax error: {exc.msg}", file=sys.stderr)
        return False
    for lineno, message in result.warnings:
        print(f"{path}:{lineno}: {message}", file=sys.stderr)
    if result.source == source:
        return False
    if args.diff:
        sys.stdout.writelines(
            difflib.unified_diff(
                source.splitlines(keepends=True),
                result.source.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
        )
    elif args.check:
        print(f"Would rewrite {path}", file=sys.stderr)
    else:
        path.write_bytes(result.source.encode(encoding))
        print(f"Rewriting {path}", file=sys.stderr)
    return True


def _print_table(table: MoveTable) -> None:
    for old, new in sorted(table.modules.items()):
        print(f"{old}.*  ->  {new}.*")
    for old, new in sorted(table.names.items()):
        module, _, name = old.rpartition(".")
        print(f"{old}  ->  {table.lookup(module, name) or new}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cmsupgrade",
        description="Rewrite imports of names that moved in django CMS 6 to their new locations.",
    )
    parser.add_argument("paths", nargs="*", metavar="PATH", help="Python files or directories to search recursively.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--diff", action="store_true", help="Print a diff instead of rewriting files.")
    mode.add_argument("--check", action="store_true", help="Only report files that would be rewritten.")
    mode.add_argument("--list", action="store_true", help="Print the table of moved names and exit.")
    parser.add_argument(
        "--no-strings",
        dest="strings",
        action="store_false",
        help="Leave dotted paths in string literals (e.g. mock.patch targets) alone.",
    )
    args = parser.parse_args(argv)

    table = load_move_table()
    if args.list:
        _print_table(table)
        return 0
    if not args.paths:
        parser.error("at least one PATH is required")
    if not table.names and not table.modules:
        print("No moved names found in the installed django CMS.", file=sys.stderr)
        return 0

    changed = False
    for path in iter_python_files(args.paths):
        changed |= _process(path, table, args)
    return int(changed)


if __name__ == "__main__":
    sys.exit(main())
