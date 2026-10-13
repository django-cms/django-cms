import ast
import contextlib
import io
import tempfile
import textwrap
from pathlib import Path

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
        },
        modules={"old.whole": "new.whole"},
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

    def test_unsupported_forms_warn(self):
        source = "from old.whole import *\nimport old.partial\n"
        result = self.assertRewrites(source, source)
        self.assertEqual([line for line, _ in result.warnings], [1, 2])

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
    """Registry entries of django CMS itself, without the fakes other tests declare."""
    _import_cms_tree()
    return [entry for entry in registry() if not entry.old_path.startswith("cms.tests.")]


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
