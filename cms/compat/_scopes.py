"""Python name scopes, as far as ``cmsupgrade`` needs them.

``cmsupgrade`` rewrites ``module.name`` references made through an imported
module. Matching references by spelling is not enough: a parameter or a local
variable may share the name of a module imported elsewhere in the file. This
module resolves each name reference to the scope whose binding it reads, by
Python's rules -- function, lambda, class, comprehension and annotation (type
parameter) scopes, ``global`` and ``nonlocal`` -- and records how every name is bound in every scope.
"""

import ast

__all__ = ["Scope", "Scopes"]


class Scope:
    """One Python scope and the bindings made in it."""

    def __init__(self, node: ast.AST, parent: "Scope | None", kind: str):
        self.node = node
        self.parent = parent
        #: ``"module"``, ``"function"``, ``"class"``, ``"comprehension"`` or
        #: ``"annotation"`` (the type parameters of a generic ``def``, ``class``
        #: or ``type`` statement).
        self.kind = kind
        #: Name -> how it is bound here: the import statement, or ``None`` for
        #: any other binding (assignment, parameter, ``def``, ``for`` target, ...).
        self.bindings: dict[str, list[ast.Import | ast.ImportFrom | None]] = {}
        self.globals: set[str] = set()
        self.nonlocals: set[str] = set()
        #: ``from x import *`` may bind any name here.
        self.star = False

    def module(self) -> "Scope":
        scope = self
        while scope.parent is not None:
            scope = scope.parent
        return scope

    def _enclosing(self) -> "Scope | None":
        # A class body's names are not visible to the functions nested in it.
        scope = self.parent
        while scope is not None and scope.kind == "class":
            scope = scope.parent
        return scope

    def outer_binding(self, name: str) -> "Scope | None":
        scope = self._enclosing()
        while scope is not None:
            if scope.kind == "module":
                return scope
            if name in scope.globals:
                return scope.module()
            if name in scope.bindings:
                return scope
            scope = scope._enclosing()
        return None

    def _sees_class(self) -> "Scope | None":
        # An annotation scope in a class body sees the class's names, unlike
        # the functions nested in it.
        if self.kind == "annotation" and self.parent.kind == "class":
            return self.parent
        return None

    def resolve(self, name: str) -> "Scope | None":
        """The scope whose binding of ``name`` a reference in this scope reads."""
        if name in self.globals:
            return self.module()
        if name in self.nonlocals:
            return self.outer_binding(name)
        if name in self.bindings or self.kind == "module":
            return self
        cls = self._sees_class()
        if cls is not None and name in cls.bindings:
            return cls
        return self.outer_binding(name)

    def binding_scope(self, name: str) -> "Scope":
        """The scope a binding of ``name`` made here goes to (``global``, ``nonlocal``)."""
        if name in self.globals:
            return self.module()
        if name in self.nonlocals:
            return self.outer_binding(name) or self
        return self

    def reads_uncertain(self, name: str) -> bool:
        """Whether a read of ``name`` here may see either of two bindings.

        A class body looks names up in its namespace first and falls back to the
        enclosing binding, so a read before the class binds the name sees the
        outer binding, and one after sees the class's -- statement order, which
        loops and conditions make undecidable here.
        """
        cls = self._sees_class()
        if cls is not None and name not in self.bindings:
            return cls.reads_uncertain(name)
        return (
            self.kind == "class" and name in self.bindings and name not in self.globals and name not in self.nonlocals
        )

    def read_candidates(self, name: str) -> list["Scope"]:
        """The scopes an uncertain read of ``name`` may see the binding of."""
        scope = self
        if name not in self.bindings and self._sees_class() is not None:
            scope = self._sees_class()
        return [candidate for candidate in (scope, scope.outer_binding(name)) if candidate is not None]


class Scopes:
    """The scopes of a module, and which scope every node is evaluated in."""

    def __init__(self, tree: ast.Module):
        self.module = Scope(tree, None, "module")
        #: ``id(node)`` -> scope, for import statements.
        self.scope_of: dict[int, Scope] = {}
        #: Every name read, with the scope it is read in.
        self.loads: list[tuple[ast.Name, Scope]] = []
        #: Every ``nonlocal`` name, with the scope declaring it.
        self.nonlocal_declarations: list[tuple[Scope, str]] = []
        self._stores: list[tuple[Scope, str, ast.AST | None]] = []
        self._visit(tree, self.module)
        # Apply bindings once all declarations are known: ``nonlocal`` refers to
        # a binding in an enclosing function that may come later in the source.
        deferred = []
        for scope, name, how in self._stores:
            if name in scope.globals:
                scope.module().bindings.setdefault(name, []).append(how)
            elif name in scope.nonlocals:
                deferred.append((scope, name, how))
            else:
                scope.bindings.setdefault(name, []).append(how)
        for scope, name, how in deferred:
            target = scope.outer_binding(name)
            if target is not None:
                target.bindings.setdefault(name, []).append(how)

    def _store(self, scope: Scope, name: str, how: ast.AST | None = None):
        self._stores.append((scope, name, how))

    def _visit(self, node: ast.AST, scope: Scope):
        method = getattr(self, f"_visit_{type(node).__name__}", None)
        if method is not None:
            method(node, scope)
        else:
            self._visit_children(node, scope)

    def _visit_children(self, node: ast.AST, scope: Scope):
        for child in ast.iter_child_nodes(node):
            self._visit(child, scope)

    def _visit_all(self, nodes, scope: Scope):
        for node in nodes:
            if node is not None:
                self._visit(node, scope)

    # -- bindings -----------------------------------------------------------

    def _visit_Name(self, node: ast.Name, scope: Scope):
        if isinstance(node.ctx, ast.Load):
            self.loads.append((node, scope))
        else:
            self._store(scope, node.id)

    def _visit_Import(self, node: ast.Import, scope: Scope):
        self.scope_of[id(node)] = scope
        for alias in node.names:
            self._store(scope, alias.asname or alias.name.partition(".")[0], node)

    def _visit_ImportFrom(self, node: ast.ImportFrom, scope: Scope):
        self.scope_of[id(node)] = scope
        for alias in node.names:
            if alias.name == "*":
                scope.star = True
            else:
                self._store(scope, alias.asname or alias.name, node)

    def _visit_Global(self, node: ast.Global, scope: Scope):
        scope.globals.update(node.names)

    def _visit_Nonlocal(self, node: ast.Nonlocal, scope: Scope):
        scope.nonlocals.update(node.names)
        self.nonlocal_declarations.extend((scope, name) for name in node.names)

    def _visit_ExceptHandler(self, node: ast.ExceptHandler, scope: Scope):
        if node.name:
            self._store(scope, node.name)
        self._visit_children(node, scope)

    def _visit_MatchAs(self, node, scope: Scope):
        if node.name:
            self._store(scope, node.name)
        self._visit_children(node, scope)

    def _visit_MatchStar(self, node, scope: Scope):
        if node.name:
            self._store(scope, node.name)

    def _visit_MatchMapping(self, node, scope: Scope):
        if node.rest:
            self._store(scope, node.rest)
        self._visit_children(node, scope)

    def _visit_NamedExpr(self, node: ast.NamedExpr, scope: Scope):
        # An assignment expression in a comprehension binds in the enclosing scope.
        target = scope
        while target.kind == "comprehension":
            target = target.parent
        self._store(target, node.target.id)
        self._visit(node.value, scope)

    # -- new scopes ---------------------------------------------------------

    def _bind_arguments(self, args: ast.arguments, scope: Scope):
        for arg in (*args.posonlyargs, *args.args, args.vararg, *args.kwonlyargs, args.kwarg):
            if arg is not None:
                self._store(scope, arg.arg)

    def _type_params(self, node, scope: Scope) -> Scope:
        """The scope of ``node``'s type parameters, or ``scope`` if it has none.

        ``def f[T: Bound]``, ``class C[T]`` and ``type A[T] = ...`` (Python
        3.12+) bind their parameters in an annotation scope between the
        definition and its body; bounds and defaults are read there.
        """
        type_params = getattr(node, "type_params", None)
        if not type_params:
            return scope
        inner = Scope(node, scope, "annotation")
        for param in type_params:
            self._store(inner, param.name)
        for param in type_params:
            for value in (getattr(param, "bound", None), getattr(param, "default_value", None)):
                if value is not None:
                    self._visit(value, inner)
        return inner

    def _visit_FunctionDef(self, node, scope: Scope):
        # Decorators and defaults are evaluated where the def is; annotations
        # too, unless the function has type parameters to read them with.
        self._visit_all(node.decorator_list, scope)
        self._visit_all(node.args.defaults, scope)
        self._visit_all(node.args.kw_defaults, scope)
        params = self._type_params(node, scope)
        for arg in (*node.args.posonlyargs, *node.args.args, node.args.vararg, *node.args.kwonlyargs, node.args.kwarg):
            if arg is not None and arg.annotation is not None:
                self._visit(arg.annotation, params)
        if node.returns is not None:
            self._visit(node.returns, params)
        self._store(scope, node.name)
        inner = Scope(node, params, "function")
        self._bind_arguments(node.args, inner)
        self._visit_all(node.body, inner)

    _visit_AsyncFunctionDef = _visit_FunctionDef

    def _visit_Lambda(self, node: ast.Lambda, scope: Scope):
        self._visit_all(node.args.defaults, scope)
        self._visit_all(node.args.kw_defaults, scope)
        inner = Scope(node, scope, "function")
        self._bind_arguments(node.args, inner)
        self._visit(node.body, inner)

    def _visit_ClassDef(self, node: ast.ClassDef, scope: Scope):
        self._visit_all(node.decorator_list, scope)
        params = self._type_params(node, scope)
        self._visit_all(node.bases, params)
        self._visit_all(node.keywords, params)
        self._store(scope, node.name)
        inner = Scope(node, params, "class")
        self._visit_all(node.body, inner)

    def _visit_TypeAlias(self, node, scope: Scope):
        self._store(scope, node.name.id)
        # The value is evaluated lazily, in an annotation scope of its own.
        params = self._type_params(node, scope)
        value = params if params is not scope else Scope(node, scope, "annotation")
        self._visit(node.value, value)

    def _visit_comprehension_scope(self, node, scope: Scope, results):
        # The first iterable is evaluated in the enclosing scope.
        self._visit(node.generators[0].iter, scope)
        inner = Scope(node, scope, "comprehension")
        for index, generator in enumerate(node.generators):
            if index:
                self._visit(generator.iter, inner)
            self._visit(generator.target, inner)
            self._visit_all(generator.ifs, inner)
        self._visit_all(results, inner)

    def _visit_ListComp(self, node, scope: Scope):
        self._visit_comprehension_scope(node, scope, [node.elt])

    _visit_SetComp = _visit_ListComp
    _visit_GeneratorExp = _visit_ListComp

    def _visit_DictComp(self, node, scope: Scope):
        self._visit_comprehension_scope(node, scope, [node.key, node.value])
