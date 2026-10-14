import ast
import contextlib
import io
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest import skipIf

from django.test import SimpleTestCase

from cms.compat import registry, resolve
from cms.compat.upgrade import MoveTable, load_move_table, main, rewrite_source
from cms.tests.test_compat_shims import _import_cms_tree


def _table():
    """A small, fixed move table, independent of what django CMS moves."""
    return MoveTable(
        names={
            "old.partial.moved_a": "new.a.moved_a",
            "old.partial.moved_b": "new.b.moved_b",
            "old.partial.renamed": "new.a.better_name",
            "old.whole.Model": "new.whole.Model",
            "old.chain.Thing": "old.whole.Thing",
            # A wholesale move with an exception, like cms.admin.forms.
            "old.mixed.Stays": "new.mixed.Stays",
            "old.mixed.Away": "new.other.Away",
        },
        modules={"old.whole": "new.whole", "old.mixed": "new.mixed"},
        defined={"old.partial": frozenset({"stays"}), "old.whole": frozenset({"local"})},
    )


class RewriteSourceTest(SimpleTestCase):
    def assertRewrites(self, source, expected, table=None, **kwargs):
        source, expected = textwrap.dedent(source), textwrap.dedent(expected)
        result = rewrite_source(source, table or _table(), **kwargs)
        self.assertEqual(result.source, expected)
        ast.parse(result.source)
        return result

    def test_module_swap_keeps_formatting(self):
        self.assertRewrites(
            """\
            from old.whole import (  # keep
                Model,
                Other as O,
            )
            """,
            """\
            from new.whole import (  # keep
                Model,
                Other as O,
            )
            """,
        )

    def test_split_by_new_module(self):
        self.assertRewrites(
            "from old.partial import moved_a, stays, moved_b as b, renamed\n",
            "from new.a import moved_a, better_name as renamed\n"
            "from old.partial import stays\n"
            "from new.b import moved_b as b\n",
        )

    def test_split_keeps_multiline_style_and_comments(self):
        self.assertRewrites(
            """\
            if True:
                from old.partial import (
                    moved_a,  # first
                    stays,  # second
                )
            """,
            """\
            if True:
                from new.a import (
                    moved_a,  # first
                )
                from old.partial import (
                    stays,  # second
                )
            """,
        )

    def test_statement_sharing_a_line(self):
        self.assertRewrites(
            "x = 1; from old.partial import moved_a, stays\n",
            "x = 1; from new.a import moved_a; from old.partial import stays\n",
        )

    def test_wholesale_module_fallback(self):
        self.assertRewrites("from old.whole import anything\n", "from new.whole import anything\n")

    def test_names_the_shim_defines_stay(self):
        source = "from old.whole import local\nfrom old.partial import stays, unknown\n"
        self.assertRewrites(source, source)

    def test_chained_moves_are_followed(self):
        self.assertRewrites("from old.chain import Thing\n", "from new.whole import Thing\n")

    def test_module_imported_from_parent(self):
        self.assertRewrites(
            "from old import whole\nfrom old import whole as w\n",
            "from new import whole\nfrom new import whole as w\n",
        )

    def test_import_statement(self):
        self.assertRewrites(
            "import old.whole\nimport old.whole as w, os\nx = old.whole.Model, old.whole\n",
            "import new.whole\nimport new.whole as w, os\nx = new.whole.Model, new.whole\n",
        )

    def test_import_of_partly_moved_module(self):
        """Migrations reference fields and managers as ``import a.b`` plus ``a.b.Name``."""
        self.assertRewrites(
            "import old.partial\nx = old.partial.moved_a(), old.partial.renamed\n",
            "import new.a\nx = new.a.moved_a(), new.a.better_name\n",
        )
        self.assertRewrites(
            "import old.partial\nx = old.partial.moved_b, old.partial.stays\n",
            "import old.partial\nimport new.b\nx = new.b.moved_b, old.partial.stays\n",
        )

    def test_unsupported_forms_warn(self):
        source = "from old.whole import *\n"
        result = self.assertRewrites(source, source)
        self.assertEqual([line for line, _ in result.warnings], [1])

    def test_aliased_import_of_partly_moved_module(self):
        self.assertRewrites(
            "import old.partial as p\nx = p.moved_a, p.stays\n",
            "import old.partial as p\nimport new.a\nx = new.a.moved_a, p.stays\n",
        )
        self.assertRewrites(
            "from old import partial\nx = partial.moved_b\n",
            "import new.b\nx = new.b.moved_b\n",
        )

    def test_fallback_with_exceptions(self):
        """A name that did not move to the fallback is not looked up there."""
        self.assertRewrites(
            "import old.mixed\nx = old.mixed.Stays, old.mixed.Away, old.mixed.Other\n",
            "import new.mixed\nimport new.other\nx = new.mixed.Stays, new.other.Away, new.mixed.Other\n",
        )
        self.assertRewrites(
            "import old.mixed as m\nx = m.Stays, m.Away\n",
            "import new.mixed as m\nimport new.other\nx = m.Stays, new.other.Away\n",
        )
        self.assertRewrites(
            "from old import mixed, whole\nx = mixed.Away, whole.Model\n",
            "from new import whole\nimport new.other\nx = new.other.Away, whole.Model\n",
        )

    def test_fallback_with_exceptions_used_as_module(self):
        """Passing the module around may read any name from it: leave it alone."""
        source = "from old import mixed\nhandler(mixed)\nx = mixed.Away\n"
        result = self.assertRewrites(source, source)
        self.assertEqual([line for line, _ in result.warnings], [2])

    def test_admin_forms(self):
        """The case that broke: two forms of cms.admin.forms moved to core, the rest to pages."""
        table = load_move_table()
        for source in (
            "import cms.admin.forms\nx = cms.admin.forms.RequestToolbarForm, cms.admin.forms.ChangePageForm\n",
            "import cms.admin.forms as f\nx = f.RequestToolbarForm, f.ChangePageForm\n",
            "from cms.admin import forms\nx = forms.RequestToolbarForm, forms.ChangePageForm\n",
        ):
            with self.subTest(source=source):
                namespace = {}
                exec(rewrite_source(source, table).source, namespace)  # noqa: S102
                self.assertIs(namespace["x"][0], resolve("cms.core.admin.forms.RequestToolbarForm"))
                self.assertIs(namespace["x"][1], resolve("cms.pages.admin.forms.ChangePageForm"))

    def test_relative_imports_untouched(self):
        source = "from .old.whole import Model\nfrom . import whole\n"
        self.assertRewrites(source, source)

    def test_strings(self):
        self.assertRewrites(
            """\
            patch("old.whole.Model.objects")
            patch('old.partial.moved_a')
            patch(r"old.partial.renamed")
            keep = ["old.whole", "old.partial.stays", f"old.whole.{x}", "old.whole" ".Model"]
            """,
            """\
            patch("new.whole.Model.objects")
            patch('new.a.moved_a')
            patch(r"new.a.better_name")
            keep = ["old.whole", "old.partial.stays", f"old.whole.{x}", "old.whole" ".Model"]
            """,
        )

    def test_strings_can_be_disabled(self):
        source = 'patch("old.whole.Model")\n'
        self.assertRewrites(source, source, strings=False)

    def test_non_ascii_offsets(self):
        self.assertRewrites(
            'x = "ünï"; from old.partial import moved_a, stays\n',
            'x = "ünï"; from new.a import moved_a; from old.partial import stays\n',
        )


def _cms_moves():
    """Every move django CMS declares."""
    _import_cms_tree()
    return registry()


class ScopeTest(SimpleTestCase):
    """References are matched to the import they read, by Python's scoping rules."""

    def assertRewrites(self, source, expected, warnings=()):
        source, expected = textwrap.dedent(source), textwrap.dedent(expected)
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, expected)
        self.assertEqual([line for line, _ in result.warnings], list(warnings))

    def test_repeated_import_rewrites_each_reference_once(self):
        self.assertRewrites(
            """\
            import old.partial
            import old.partial
            x = old.partial.moved_a
            """,
            """\
            import new.a
            import new.a
            x = new.a.moved_a
            """,
        )

    def test_local_imports_in_separate_functions(self):
        self.assertRewrites(
            """\
            def f():
                from old import partial
                return partial.moved_a

            def g():
                from old import partial
                return partial.moved_a
            """,
            """\
            def f():
                import new.a
                return new.a.moved_a

            def g():
                import new.a
                return new.a.moved_a
            """,
        )

    def test_parameter_shadows_the_module(self):
        self.assertRewrites(
            """\
            import old.partial as partial

            def f(partial):
                return partial.moved_a()

            y = partial.moved_a
            """,
            """\
            import new.a

            def f(partial):
                return partial.moved_a()

            y = new.a.moved_a
            """,
        )

    def test_class_body_and_comprehension_names(self):
        """A class attribute is not visible in methods; a comprehension variable is local.

        Reads in the class body itself are order-dependent, see
        ``test_class_body_read_before_class_binding``.
        """
        self.assertRewrites(
            """\
            from old import partial
            class A:
                partial = None
                def m(self):
                    return partial.moved_a
            y = [partial.moved_a for partial in z]
            """,
            """\
            import new.a
            class A:
                partial = None
                def m(self):
                    return new.a.moved_a
            y = [partial.moved_a for partial in z]
            """,
        )

    def test_global_and_nonlocal(self):
        self.assertRewrites(
            """\
            from old import partial
            def f():
                global partial
                return partial.moved_a
            def g():
                partial = None
                def h():
                    nonlocal partial
                    return partial.moved_a
            """,
            """\
            import new.a
            def f():
                global partial
                return new.a.moved_a
            def g():
                partial = None
                def h():
                    nonlocal partial
                    return partial.moved_a
            """,
        )

    def test_nonlocal_keeps_the_import(self):
        """``nonlocal partial`` needs the enclosing binding, even with no reference left."""
        self.assertRewrites(
            """\
            def g():
                from old import partial
                def h():
                    nonlocal partial
                    return partial.moved_a
            """,
            """\
            def g():
                from old import partial
                import new.a
                def h():
                    nonlocal partial
                    return new.a.moved_a
            """,
        )

    @skipIf(sys.version_info < (3, 12), "type parameter syntax")
    def test_type_parameters(self):
        """Bounds are references; type parameters shadow imports of the same name."""
        self.assertRewrites(
            """\
            from old import partial
            class C[T: partial.moved_a](partial.moved_b):
                pass
            def f[T: partial.moved_a](x: T) -> partial.moved_b:
                pass
            type A[T: partial.moved_a] = list[partial.moved_b]
            """,
            """\
            import new.a
            import new.b
            class C[T: new.a.moved_a](new.b.moved_b):
                pass
            def f[T: new.a.moved_a](x: T) -> new.b.moved_b:
                pass
            type A[T: new.a.moved_a] = list[new.b.moved_b]
            """,
        )
        self.assertRewrites(
            """\
            from old import partial
            def f[partial](x: partial.moved_a):
                pass
            y = partial.moved_a
            """,
            """\
            import new.a
            def f[partial](x: partial.moved_a):
                pass
            y = new.a.moved_a
            """,
        )

    @skipIf(sys.version_info < (3, 12), "type parameter syntax")
    def test_type_parameters_see_the_class(self):
        """Unlike a method, a type parameter bound in a class body reads the class's names."""
        source = textwrap.dedent(
            """\
            from old import partial
            class A:
                partial = None
                def m[T: partial.moved_a](self):
                    pass
            y = partial.moved_a
            """
        )
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, source)
        self.assertEqual(len(result.warnings), 1)

    def test_name_bound_otherwise_is_left_alone(self):
        for source in (
            "from old import partial\npartial = wrap(partial)\nx = partial.moved_a\n",
            "try:\n    from old import partial\nexcept ImportError:\n    from other import partial\nx = partial.moved_a\n",
            "from old import partial\nfrom elsewhere import *\nx = partial.moved_a\n",
        ):
            with self.subTest(source=source):
                result = rewrite_source(source, _table())
                self.assertEqual(result.source, source)
                self.assertEqual(len(result.warnings), 1)

    def test_global_import_binds_at_module_level(self):
        """``global`` moves the binding: references at module level read it."""
        self.assertRewrites(
            """\
            def setup():
                global mixed
                import old.mixed as mixed
            x = mixed.Stays
            """,
            """\
            def setup():
                global mixed
                import new.mixed as mixed
            x = mixed.Stays
            """,
        )
        # A name that moved elsewhere would need ``new`` at module level, where
        # the import added in ``setup`` does not bind it: left alone.
        source = "def setup():\n    global mixed\n    import old.mixed as mixed\nx = mixed.Away\n"
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, source)
        self.assertEqual([line for line, _ in result.warnings], [3])

    def test_destination_name_shadowed_at_the_reference(self):
        """The rewritten reference must read the package, not a parameter named like it."""
        source = textwrap.dedent(
            """\
            from old import partial

            def f(new):
                return partial.moved_a
            """
        )
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, source)
        self.assertEqual([line for line, _ in result.warnings], [1])

    def test_class_body_read_before_class_binding(self):
        """A class body may read the outer import before binding the name itself."""
        source = textwrap.dedent(
            """\
            from old import partial

            class A:
                x = partial.stays
                partial = None

            y = partial.moved_a
            """
        )
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, source)
        self.assertEqual([line for line, _ in result.warnings], [1])

    def test_new_import_must_not_rebind_the_package_name(self):
        # ``new`` is read from the module scope before the new import would bind it locally.
        source = textwrap.dedent(
            """\
            import new.thing
            def f():
                x = new.thing
                from old import partial
                return partial.moved_a, x
            """
        )
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, source)
        self.assertEqual([line for line, _ in result.warnings], [4])
        # ``new`` is something else in this scope.
        source = "new = 1\nfrom old import partial\nx = partial.moved_a\n"
        result = rewrite_source(source, _table())
        self.assertEqual(result.source, source)
        self.assertEqual(len(result.warnings), 1)


class MoveTableTest(SimpleTestCase):
    def test_static_table_matches_registry(self):
        """Reading ``moved()`` declarations statically finds every runtime entry."""
        table = load_move_table()
        for entry in _cms_moves():
            with self.subTest(old=entry.old_path):
                self.assertEqual(table.names[entry.old_path], entry.new_path)

    def test_rewritten_imports_resolve(self):
        """Every moved name, imported through the rewritten statement, is the same object."""
        table = load_move_table()
        for entry in _cms_moves():
            module, _, name = entry.old_path.rpartition(".")
            with self.subTest(old=entry.old_path):
                (node,) = ast.parse(rewrite_source(f"from {module} import {name}\n", table).source).body
                self.assertNotEqual(node.module, module)
                self.assertIs(resolve(f"{node.module}.{node.names[0].name}"), resolve(entry.old_path))


    def test_rewritten_module_references_resolve(self):
        """Every moved name, reached through a rewritten module import, is the same object.

        Module imports follow the shim's ``fallback``, but some names of a module
        moved elsewhere (``cms.admin.forms.RequestToolbarForm``); this covers all of
        them for each way of importing a module.
        """
        table = load_move_table()
        for entry in _cms_moves():
            module, _, name = entry.old_path.rpartition(".")
            parent, _, base = module.rpartition(".")
            for source in (
                f"import {module}\nx = {module}.{name}\n",
                f"import {module} as m\nx = m.{name}\n",
                f"from {parent} import {base}\nx = {base}.{name}\n",
            ):
                with self.subTest(old=entry.old_path, form=source.partition("\n")[0]):
                    rewritten = rewrite_source(source, table).source
                    self.assertNotIn(f"{module}.", rewritten.replace(f"import {module}\n", ""))
                    namespace = {}
                    exec(rewritten, namespace)  # noqa: S102
                    self.assertIs(namespace["x"], resolve(entry.old_path))


class CommandTest(SimpleTestCase):
    def run_command(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = main(list(args))
        return status, stdout.getvalue(), stderr.getvalue()

    def test_recursive_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app" / "sub").mkdir(parents=True)
            (root / ".venv").mkdir()
            (root / ".venv" / "pyvenv.cfg").write_text("")
            moved = "from cms.plugin_base import CMSPluginBase\r\n"
            target = root / "app" / "sub" / "cms_plugins.py"
            target.write_bytes(moved.encode())
            (root / ".venv" / "lib.py").write_bytes(moved.encode())
            (root / "app" / "clean.py").write_text("import os\n")
            (root / "app" / "broken.py").write_text("def (\n")

            status, _, stderr = self.run_command("--check", tmp)
            self.assertEqual(status, 1)
            self.assertIn("cms_plugins.py", stderr)
            self.assertIn("syntax error", stderr)
            self.assertEqual(target.read_bytes(), moved.encode())

            status, _, _ = self.run_command(tmp)
            self.assertEqual(status, 1)
            self.assertEqual(target.read_bytes(), b"from cms.core.plugin_base import CMSPluginBase\r\n")
            self.assertEqual((root / ".venv" / "lib.py").read_bytes(), moved.encode())

            status, _, _ = self.run_command(tmp)
            self.assertEqual(status, 0)

    def test_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.py"
            path.write_text("from cms.plugin_pool import plugin_pool\n")
            status, stdout, _ = self.run_command("--diff", str(path))
            self.assertEqual(status, 1)
            self.assertIn("+from cms.core.plugin_pool import plugin_pool", stdout)
            self.assertEqual(path.read_text(), "from cms.plugin_pool import plugin_pool\n")

    def test_list(self):
        status, stdout, _ = self.run_command("--list")
        self.assertEqual(status, 0)
        self.assertIn("cms.plugin_base.CMSPluginBase  ->  cms.core.plugin_base.CMSPluginBase", stdout)
