"""
Coverage-completing tests for cms.utils.mptree.

The functional behaviour is already exercised by test_mptree_backend /
test_mptree_prototype and the real page suites. This module targets the code
paths django-cms itself does not happen to hit:

* ``MaterializedPathDriverTests`` drives the low-level ``MaterializedPath``
  against the treebeard-shaped ``Category`` model -- add_sibling, first-child
  insert, scope, lock-disabled, move guards, etc.
* ``MaterializedPathMixinCoverageTests`` covers mixin methods that ``Page``
  overrides (``get_root``/``delete``) or never calls (the treebeard-compat
  predicates).

Both classes test the mptree implementation, so the module only runs under that
backend (``CMS_TREE_BACKEND=mptree``) and is skipped under treebeard.
"""

from unittest import skipUnless

from django.test import TestCase

from cms.api import create_page
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mptree import MaterializedPath, MaterializedPathMixin, get_tree_backend

TEMPLATE = "nav_playground.html"

mptree_only = skipUnless(
    get_tree_backend() == "mptree",
    "mptree backend only -- run with CMS_TREE_BACKEND=mptree",
)


@mptree_only
class MaterializedPathDriverTests(TestCase):
    def setUp(self):
        self.mp = MaterializedPath(Category)

    def test_tree_root_of_and_empty_ancestors(self):
        r = self.mp.add_root(name="r")
        c = self.mp.add_child(r, name="c")
        g = self.mp.add_child(c, name="g")

        self.assertEqual(self.mp.tree().count(), 3)                       # parent=None
        self.assertEqual(
            set(self.mp.tree(r).values_list("name", flat=True)),         # parent given
            {"r", "c", "g"},
        )
        self.assertEqual(self.mp.root_of(g).pk, r.pk)
        self.assertEqual(list(self.mp.ancestors(r)), [])                 # root has none

    def test_add_child_first_child(self):
        r = self.mp.add_root(name="r")
        self.mp.add_child(r, name="a")
        self.mp.add_child(r, name="b")
        self.mp.add_child(r, position="first-child", name="c")
        self.assertEqual(
            list(self.mp.children(r).values_list("name", flat=True)),
            ["c", "a", "b"],
        )

    def test_add_sibling_all_positions(self):
        r = self.mp.add_root(name="r")
        a = self.mp.add_child(r, name="a")
        b = self.mp.add_child(r, name="b")

        # child siblings -> _place_relative (after True/False) + last/first
        self.mp.add_sibling(a, name="s_last")                  # default last-sibling
        self.mp.add_sibling(a, position="right", name="s_right")
        self.mp.add_sibling(b, position="left", name="s_left")
        self.mp.add_sibling(b, position="first-sibling", name="s_first")

        # root siblings -> parent-None branch (last + left/no-op)
        self.mp.add_sibling(r, name="r2")
        self.mp.add_sibling(r, position="left", name="r3")

        self.assertEqual(self.mp.roots().count(), 3)
        self.assertEqual(Category.objects.count(), 9)
        # every node still has a path correctly nested under its parent
        for cat in Category.objects.all():
            if cat.parent_id:
                self.assertTrue(cat.path.startswith(cat.parent.path))

    def test_move_left_and_right_into_middle(self):
        r = self.mp.add_root(name="r")
        a = self.mp.add_child(r, name="a")
        self.mp.add_child(r, name="b")
        c = self.mp.add_child(r, name="c")

        self.mp.move(c, a, "left")   # left, lands mid-group -> _layout
        self.assertEqual(
            list(self.mp.children(r).values_list("name", flat=True)), ["c", "a", "b"]
        )
        self.mp.move(c, a, "right")  # right, lands mid-group -> _layout
        self.assertEqual(
            list(self.mp.children(r).values_list("name", flat=True)), ["a", "c", "b"]
        )

    def test_positional_move_landing_at_end(self):
        r = self.mp.add_root(name="r")
        a = self.mp.add_child(r, name="a")
        b = self.mp.add_child(r, name="b")

        # 'right' of the last sibling -> append branch (siblings non-empty)
        self.mp.move(a, b, "right")
        self.assertEqual(
            list(self.mp.children(r).values_list("name", flat=True)), ["b", "a"]
        )
        # 'first-child' of a leaf -> append branch with empty siblings
        self.mp.move(b, a, "first-child")
        self.assertEqual(self.mp.children(a).first().name, "b")

    def test_move_out_from_under_a_shifted_sibling(self):
        # Regression: the node being moved lives *inside* a sibling that the
        # layout has to shift. Rewriting that sibling's subtree first used to
        # drag the node along, so its own rewrite then matched nothing and it
        # stayed buried (admin "move to root position N" hit exactly this).
        gamma = self.mp.add_root(name="gamma")
        delta = self.mp.add_child(gamma, name="delta")

        self.mp.move(delta, gamma, "left")  # left of its own parent

        delta.refresh_from_db()
        gamma.refresh_from_db()
        self.assertEqual(
            list(self.mp.roots().values_list("name", flat=True)), ["delta", "gamma"]
        )
        self.assertEqual((delta.depth, delta.parent_id), (1, None))
        self.assertEqual(self.mp.descendants(gamma).count(), 0)
        self.assertEqual(gamma.numchild, 0)

    def test_move_out_from_under_an_uncle(self):
        # Same nesting hazard one level over: `c` sits under `b`, and landing it
        # first-child of `r` shifts both `a` and `b` down a slot.
        r = self.mp.add_root(name="r")
        self.mp.add_child(r, name="a")
        b = self.mp.add_child(r, name="b")
        c = self.mp.add_child(b, name="c")

        self.mp.move(c, r, "first-child")

        c.refresh_from_db()
        b.refresh_from_db()
        self.assertEqual(
            list(self.mp.children(r).values_list("name", flat=True)), ["c", "a", "b"]
        )
        self.assertEqual((c.depth, c.parent_id), (2, r.pk))
        self.assertEqual(b.numchild, 0)

    def test_move_into_own_subtree_raises(self):
        r = self.mp.add_root(name="r")
        c = self.mp.add_child(r, name="c")
        with self.assertRaises(ValueError):
            self.mp.move(r, c, "last-child")

    def test_scope_sets_fields(self):
        # `scope` filters the forest and is stamped onto new nodes (both the
        # field-kwargs path and the explicit instance path).
        mp = MaterializedPath(Category, scope={"name": "scoped"})
        mp.add_root()
        stamped = mp.add_root(instance=Category(name="ignored"))
        self.assertEqual(stamped.name, "scoped")
        self.assertEqual(mp.roots().count(), 2)

    def test_lock_disabled(self):
        mp = MaterializedPath(Category, lock=False)
        r = mp.add_root(name="r")
        mp.add_child(r, name="c")
        self.assertEqual(mp.children(r).count(), 1)


@mptree_only
class MaterializedPathMixinCoverageTests(CMSTestCase):
    def _page(self, name, parent=None, position="last-child"):
        return create_page(name, TEMPLATE, "en", parent=parent, position=position)

    def test_treebeard_compat_predicates(self):
        root = self._page("root")
        a = self._page("a", parent=root)
        b = self._page("b", parent=a)
        for page in (root, a, b):
            page.refresh_from_db()

        a2 = self._page("a2", parent=root)
        a.refresh_from_db()
        a2.refresh_from_db()

        self.assertEqual(a.get_parent().pk, root.pk)
        self.assertEqual(root.get_first_child().pk, a.pk)
        self.assertTrue(a.is_sibling_of(a2))
        self.assertFalse(a.is_sibling_of(b))
        self.assertTrue(a.is_child_of(root))
        self.assertFalse(b.is_child_of(root))
        self.assertTrue(b.is_descendant_of(root))
        self.assertFalse(root.is_descendant_of(b))
        self.assertIn(root.pk, [s.pk for s in root.get_siblings()])   # root branch
        self.assertIn(a.pk, [s.pk for s in a.get_siblings()])         # child branch

        # get_root is overridden on Page -> exercise the mixin's directly
        self.assertEqual(MaterializedPathMixin.get_root(b).pk, root.pk)

    def test_add_sibling_via_position(self):
        root = self._page("root")
        a = self._page("a", parent=root)
        # position "left" routes Page.add_to_tree -> Page.add_sibling -> mixin
        self._page("left-of-a", parent=a, position="left")
        root.refresh_from_db()
        # first-child into a branch -> get_first_child().add_sibling(...)
        self._page("first", parent=root, position="first-child")
        self.assertGreaterEqual(root.get_child_pages().count(), 1)

    def test_mixin_delete_decrements_numchild(self):
        root = self._page("root")
        leaf = self._page("leaf", parent=root)
        leaf.refresh_from_db()
        # Page overrides delete(); call the mixin implementation directly.
        MaterializedPathMixin.delete(leaf)
        root.refresh_from_db()
        self.assertEqual(root.numchild, 0)
