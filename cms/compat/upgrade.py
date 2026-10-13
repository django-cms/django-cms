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
* String literals holding a dotted path to a moved name, typically
  ``mock.patch("cms.plugin_pool.plugin_pool")`` targets. Disable with
  ``--no-strings``.

Star imports from a moved module, and plain ``import`` of a module that only
moved in part, are reported but left alone.

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


def _rewrite_import_from(node, table, offsets, edits, warnings):
    if node.level or not node.module:
        return
    module = node.module
    shims = table.shim_modules()
    if any(alias.name == "*" for alias in node.names):
        if module in shims:
            warnings.append((node.lineno, f"star import from moved module {module}; update it manually"))
        return

    # (new module, imported name, local name) per alias, in order.
    targets = []
    for alias in node.names:
        local = alias.asname or alias.name
        new_path = table.lookup(module, alias.name)
        if new_path is None:
            new_path = table.module_target(f"{module}.{alias.name}")
        if new_path is None:
            targets.append((module, alias.name, local))
        else:
            new_module, _, new_name = new_path.rpartition(".")
            targets.append((new_module, new_name, local))
    if all(new_module == module for new_module, _, _ in targets):
        return

    start, end = offsets.span(node)
    statement = offsets.source[start:end]
    new_modules = {new_module for new_module, _, _ in targets}
    names_kept = all(alias.name == name for alias, (_, name, _) in zip(node.names, targets, strict=True))
    match = _FROM_MODULE.match(statement)
    if len(new_modules) == 1 and names_kept and match:
        # Only the module changed: swap it and keep the rest, comments included.
        edits.append((start + match.start(1), start + match.end(1), new_modules.pop()))
        return

    multiline = "\n" in statement and "(" in statement
    comments, dropped = _alias_comments(node, statement) if multiline else ({}, 0)
    if dropped:
        warnings.append((node.lineno, f"comments inside the import from {module} were dropped"))
    groups: dict[str, list[tuple[str, str]]] = {}
    for index, (new_module, name, local) in enumerate(targets):
        groups.setdefault(new_module, []).append((_format_alias(name, local), comments.get(index, "")))
    prefix = offsets.line_prefix(start)
    indent = prefix if not prefix.strip() else ""
    separator = f"\n{indent}" if not prefix.strip() else "; "
    replacement = separator.join(
        _format_from(new_module, aliases, multiline, indent) for new_module, aliases in groups.items()
    )
    edits.append((start, end, replacement))


def _rewrite_import(node, table, offsets, edits, warnings, plain_imports):
    aliases = []
    changed = False
    for alias in node.names:
        target = table.module_target(alias.name)
        if target is None:
            if alias.name in table.shim_modules():
                warnings.append((node.lineno, f"{alias.name} moved in part; update references to its names manually"))
            aliases.append(_format_alias(alias.name, alias.asname))
            continue
        changed = True
        if alias.asname is None:
            plain_imports[alias.name] = target
        aliases.append(_format_alias(target, alias.asname))
    if changed:
        start, end = offsets.span(node)
        edits.append((start, end, f"import {', '.join(aliases)}"))


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
    plain_imports: dict[str, str] = {}
    shims = table.shim_modules()

    in_fstring = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            in_fstring.update(id(sub) for sub in ast.walk(node))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            _rewrite_import_from(node, table, offsets, edits, warnings)
        elif isinstance(node, ast.Import):
            _rewrite_import(node, table, offsets, edits, warnings, plain_imports)
        elif strings and isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in in_fstring:
            _rewrite_string(node, table, shims, offsets, edits)

    if plain_imports:
        # ``import cms.plugin_pool`` was rewritten, so its references must follow.
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and _dotted(node) in plain_imports:
                start, end = offsets.span(node)
                edits.append((start, end, plain_imports[_dotted(node)]))

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
