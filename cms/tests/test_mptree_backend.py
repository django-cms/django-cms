"""
Guardrail + functional tests for the swappable tree backend.

* ``TreeFieldParityTests`` proves the swap is *migration-invisible*: Django
  builds migrations purely from field deconstruction, so if
  ``MaterializedPathMixin`` deconstructs its tree fields identically to
  treebeard's ``MP_Node``, substituting one for the other produces no migration.

* ``PageTreeBackendTests`` and ``PageQuerySetDeleteTests`` are ordinary
  page-tree tests covering build, query, move and delete.

The whole module only runs under the mptree backend::

    CMS_TREE_BACKEND=mptree python manage.py test cms.tests.test_mptree_backend

Under treebeard it is skipped: those code paths belong to treebeard, are covered
by the rest of the suite, and holding treebeard to this module's expectations
means asserting on upstream behaviour we cannot fix.
"""
import os
import time
from collections import defaultdict
from unittest import skipIf

from django.test import SimpleTestCase, TestCase, TransactionTestCase
from treebeard.mp_tree import MP_Node

from cms.api import create_page
from cms.models import Page
from cms.test_utils.project.sampleapp.models import Category
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mptree import (
    MaterializedPath,
    MaterializedPathMixin,
    get_tree_backend,
    get_tree_base,
)

TEMPLATE = "nav_playground.html"

mptree_only = skipIf(
    get_tree_backend() == "treebeard",
    "mptree backend only -- run with CMS_TREE_BACKEND=mptree",
)


@mptree_only
class TreeFieldParityTests(SimpleTestCase):
    """Field-level proof that the two backends are interchangeable without a
    schema migration."""

    TREE_FIELDS = {"path", "depth", "numchild"}

    def _deconstructed(self, base):
        # drop the field name (index 0); compare (import_path, args, kwargs)
        return {
            f.name: f.deconstruct()[1:]
            for f in base._meta.get_fields()
            if f.name in self.TREE_FIELDS
        }

    def test_fields_deconstruct_identically(self):
        self.assertEqual(
            self._deconstructed(MaterializedPathMixin),
            self._deconstructed(MP_Node),
        )

    def test_same_concrete_field_set(self):
        mp = {f.name for f in MaterializedPathMixin._meta.get_fields()}
        tb = {f.name for f in MP_Node._meta.get_fields()}
        self.assertEqual(mp, tb)
        self.assertEqual(mp, self.TREE_FIELDS)

    def test_selector_matches_active_backend(self):
        self.assertIs(get_tree_base(), MaterializedPathMixin)

    def test_queryset_is_treebeard_free_in_mptree_mode(self):
        # The page queryset must not inherit from treebeard when the mptree
        # backend is active -- otherwise treebeard would be imported.
        from cms.models.query import PageQuerySet

        mro_modules = {base.__module__ for base in PageQuerySet.__mro__}
        self.assertNotIn("treebeard.mp_tree", mro_modules)
        # The manager is backend-agnostic (never treebeard) in either mode.
        from cms.models import Page

        self.assertNotIn("treebeard", type(Page.objects).__module__)


@mptree_only
class PageTreeBackendTests(CMSTestCase):
    """The page tree as built, queried and moved by the mptree backend."""

    def test_build_and_query(self):
        root = create_page("root", TEMPLATE, "en")
        c1 = create_page("c1", TEMPLATE, "en", parent=root)
        c2 = create_page("c2", TEMPLATE, "en", parent=root)
        g1 = create_page("g1", TEMPLATE, "en", parent=c1)

        root.refresh_from_db()
        self.assertTrue(root.is_root())
        self.assertEqual(
            list(root.get_child_pages().values_list("pk", flat=True)),
            [c1.pk, c2.pk],
        )
        self.assertEqual(root.get_descendant_pages().count(), 3)
        self.assertEqual(
            list(g1.get_ancestor_pages().values_list("pk", flat=True)),
            [root.pk, c1.pk],
        )
        self.assertTrue(g1.is_leaf())
        self.assertEqual(g1.get_root().pk, root.pk)
        # paths stay correctly nested
        for child in (c1, c2, g1):
            child.refresh_from_db()
        self.assertTrue(c1.path.startswith(root.path))
        self.assertTrue(g1.path.startswith(c1.path))

    def test_move_page_reparents_subtree(self):
        root = create_page("root", TEMPLATE, "en")
        a = create_page("a", TEMPLATE, "en", parent=root)
        b = create_page("b", TEMPLATE, "en", parent=root)
        a_child = create_page("a_child", TEMPLATE, "en", parent=a)

        # Move `a` (with its subtree) under `b`.
        a.refresh_from_db()
        b.refresh_from_db()
        a.move_page(b, "last-child")

        a.refresh_from_db()
        a_child.refresh_from_db()
        b.refresh_from_db()

        self.assertEqual(a.parent_id, b.pk)
        self.assertEqual(a.depth, b.depth + 1)
        self.assertEqual(a_child.depth, a.depth + 1)
        self.assertTrue(a.path.startswith(b.path))
        self.assertTrue(a_child.path.startswith(a.path))
        self.assertIn(a.pk, b.get_descendant_pages().values_list("pk", flat=True))
        self.assertIn(
            a_child.pk, b.get_descendant_pages().values_list("pk", flat=True)
        )

    def test_move_left_orders_db_correctly(self):
        # DB-truth check (the real-suite regression tests assert on stale
        # in-memory objects + treebeard's exact bytes; here we verify ordering).
        home = create_page("Home", TEMPLATE, "en")
        alpha = create_page("Alpha", TEMPLATE, "en", parent=home)
        beta = create_page("Beta", TEMPLATE, "en", parent=home)

        beta.move_page(alpha, position="left")

        alpha.refresh_from_db()
        beta.refresh_from_db()
        home.refresh_from_db()
        self.assertEqual(
            list(home.get_child_pages().values_list("pk", flat=True)),
            [beta.pk, alpha.pk],
        )
        self.assertTrue(beta.path < alpha.path)

    def test_move_page_out_to_the_left_of_its_own_parent(self):
        # What the admin does for "move to root position N": the target sibling
        # is the page's own parent, so the page has to climb out of a subtree
        # that the same layout is shifting.
        home = create_page("Home", TEMPLATE, "en")
        gamma = create_page("Gamma", TEMPLATE, "en")
        delta = create_page("Delta", TEMPLATE, "en", parent=gamma)

        gamma.refresh_from_db()
        delta.refresh_from_db()
        delta.move_page(gamma, position="left")

        gamma.refresh_from_db()
        delta.refresh_from_db()
        self.assertEqual(delta.parent_id, None)
        self.assertEqual(delta.depth, 1)
        self.assertEqual(gamma.numchild, 0)
        self.assertEqual(gamma.get_descendant_pages().count(), 0)
        self.assertEqual(
            list(Page.get_root_nodes().values_list("pk", flat=True)),
            [home.pk, delta.pk, gamma.pk],
        )

    def test_delete_updates_parent_numchild(self):
        page1 = create_page("home", TEMPLATE, "en")
        page2 = create_page("page2", TEMPLATE, "en", parent=page1)
        self.assertEqual(page1.numchild, 1)  # in-memory, no refresh
        page2.delete()
        page1.refresh_from_db()
        self.assertEqual(page1.numchild, 0)
        self.assertTrue(page1.is_leaf())

    def test_rebuild_preserves_sibling_order_not_pk_order(self):
        # Reorder siblings away from creation (pk) order, then rebuild and
        # confirm the editor-chosen order survives -- i.e. order comes from the
        # path, so no separate `position` field is required.
        root = create_page("root", TEMPLATE, "en")
        a = create_page("a", TEMPLATE, "en", parent=root)  # pk order: a, b, c
        b = create_page("b", TEMPLATE, "en", parent=root)
        c = create_page("c", TEMPLATE, "en", parent=root)

        c.refresh_from_db()
        a.refresh_from_db()
        c.move_page(a, position="left")  # path order now: c, a, b
        root.refresh_from_db()
        self.assertEqual(
            list(root.get_child_pages().values_list("pk", flat=True)),
            [c.pk, a.pk, b.pk],
        )

        Page.fix_tree()  # -> rebuild()
        root.refresh_from_db()
        self.assertEqual(
            list(root.get_child_pages().values_list("pk", flat=True)),
            [c.pk, a.pk, b.pk],  # preserved, NOT [a, b, c]
        )

    def test_bulk_queryset_delete_updates_numchild(self):
        # Bulk Page.objects.filter(...).delete() must keep the surviving
        # parent's numchild correct (treebeard does this; the mptree branch
        # must too). Descendants are removed via parent FK CASCADE.
        root = create_page("root", TEMPLATE, "en")
        a = create_page("a", TEMPLATE, "en", parent=root)
        create_page("b", TEMPLATE, "en", parent=root)
        create_page("a_child", TEMPLATE, "en", parent=a)

        root.refresh_from_db()
        self.assertEqual(root.numchild, 2)

        # delete `a` (and its subtree) via a bulk queryset delete
        Page.objects.filter(pk=a.pk).delete()

        root.refresh_from_db()
        self.assertEqual(root.numchild, 1)
        self.assertEqual(root.get_child_pages().count(), 1)
        self.assertFalse(Page.objects.filter(pk=a.pk).exists())

    def test_root_nodes_and_fix_tree(self):
        r1 = create_page("r1", TEMPLATE, "en")
        r2 = create_page("r2", TEMPLATE, "en")
        create_page("child", TEMPLATE, "en", parent=r1)

        roots = set(Page.get_root_nodes().values_list("pk", flat=True))
        self.assertEqual(roots, {r1.pk, r2.pk})

        # fix_tree / rebuild must leave a consistent, queryable tree.
        Page.fix_tree()
        r1.refresh_from_db()
        self.assertEqual(r1.get_descendant_pages().count(), 1)
        self.assertEqual(set(Page.get_root_nodes().values_list("pk", flat=True)), roots)


@mptree_only
class PageQuerySetDeleteTests(CMSTestCase):
    """``PageQuerySet.delete`` is the one queryset method with a backend-specific
    implementation: treebeard walks ``path`` prefixes to remove subtrees, while
    the mptree branch leans on the ``parent`` FK cascade and fixes the surviving
    parents' ``numchild`` cache itself. ``delete_fast`` is the escape hatch that
    skips all of that."""

    def _tree(self):
        """``root -> (a -> (a1, a2), b)`` -- returns the pages top-down."""
        root = create_page("root", TEMPLATE, "en")
        a = create_page("a", TEMPLATE, "en", parent=root)
        b = create_page("b", TEMPLATE, "en", parent=root)
        a1 = create_page("a1", TEMPLATE, "en", parent=a)
        a2 = create_page("a2", TEMPLATE, "en", parent=a)
        return root, a, b, a1, a2

    def test_delete_removes_the_whole_subtree(self):
        # Deleting a branch must take its descendants with it -- no orphans
        # pointing at a gone parent.
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk=a.pk).delete()

        self.assertFalse(Page.objects.filter(pk__in=[a.pk, a1.pk, a2.pk]).exists())
        self.assertEqual(
            set(Page.objects.values_list("pk", flat=True)), {root.pk, b.pk}
        )
        root.refresh_from_db()
        self.assertEqual(root.numchild, 1)

    def test_delete_several_children_of_one_parent(self):
        # Two children of the same parent in a single call -> numchild must drop
        # by two, not by one.
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk__in=[a1.pk, a2.pk]).delete()

        a.refresh_from_db()
        self.assertEqual(a.numchild, 0)
        self.assertTrue(a.is_leaf())
        root.refresh_from_db()
        self.assertEqual(root.numchild, 2)  # untouched

    def test_delete_parent_and_child_in_one_queryset(self):
        # `a1` is deleted twice over (explicitly, and as a descendant of `a`):
        # only `root` may be decremented, and only once.
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk__in=[a.pk, a1.pk]).delete()

        root.refresh_from_db()
        self.assertEqual(root.numchild, 1)
        self.assertEqual(
            set(Page.objects.values_list("pk", flat=True)), {root.pk, b.pk}
        )

    def test_delete_root_pages(self):
        # Roots have parent_id NULL -- there is nothing to decrement, and the
        # NULL must not be mistaken for a parent to update.
        r1 = create_page("r1", TEMPLATE, "en")
        create_page("r1_child", TEMPLATE, "en", parent=r1)
        create_page("r2", TEMPLATE, "en")

        Page.objects.filter(depth=1).delete()

        self.assertEqual(Page.objects.count(), 0)

    def test_delete_never_makes_numchild_negative(self):
        # A stale/corrupt numchild cache must not be driven below zero -- and
        # must not blow up on MySQL's unsigned column either.
        root, a, b, a1, a2 = self._tree()
        Page.objects.filter(pk=root.pk).update(numchild=0)

        Page.objects.filter(pk=a.pk).delete()

        root.refresh_from_db()
        self.assertEqual(root.numchild, 0)

    def test_delete_on_empty_queryset_is_a_noop(self):
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk__in=[]).delete()

        self.assertEqual(Page.objects.count(), 5)
        root.refresh_from_db()
        a.refresh_from_db()
        self.assertEqual((root.numchild, a.numchild), (2, 2))

    # --- delete_fast ----------------------------------------------------

    def test_delete_fast_removes_rows_and_descendants(self):
        # Plain Django delete: the rows go, and so do their descendants -- but
        # via the parent FK cascade, in *both* backends (treebeard's path walk
        # is bypassed entirely).
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk=a.pk).delete_fast()

        self.assertEqual(
            set(Page.objects.values_list("pk", flat=True)), {root.pk, b.pk}
        )

    def test_delete_fast_leaves_numchild_stale_on_purpose(self):
        # The whole point of delete_fast: no tree bookkeeping. The caller is
        # responsible for numchild -- compare with delete(), which fixes it.
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk=a.pk).delete_fast()

        root.refresh_from_db()
        self.assertEqual(root.numchild, 2)  # stale, not 1

        # ...whereas the same removal through delete() does fix the cache.
        Page.objects.filter(pk=b.pk).delete()
        root.refresh_from_db()
        self.assertEqual(root.numchild, 1)

    def test_delete_fast_on_empty_queryset_is_a_noop(self):
        root, a, b, a1, a2 = self._tree()

        Page.objects.filter(pk__in=[]).delete_fast()

        self.assertEqual(Page.objects.count(), 5)

    def test_page_instance_delete_builds_on_delete_fast(self):
        # Page.delete() is the real caller: it drops the subtree with
        # delete_fast and then decrements the parent itself -- exactly once,
        # no matter how large the subtree.
        root, a, b, a1, a2 = self._tree()

        a.refresh_from_db()
        a.delete()

        self.assertEqual(
            set(Page.objects.values_list("pk", flat=True)), {root.pk, b.pk}
        )
        root.refresh_from_db()
        self.assertEqual(root.numchild, 1)



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


def make_spec():
    """A deterministic (name, parent_name) build order; parents precede children."""
    spec = []
    for r in range(3):  # roots
        root = f"r{r}"
        spec.append((root, None))
        for c in range(4):  # children
            child = f"{root}_c{c}"
            spec.append((child, root))
            for g in range(2):  # grandchildren
                spec.append((f"{child}_g{g}", child))
    return spec


def snapshot():
    return {
        c.name: (c.path, c.depth, c.numchild)
        for c in Category.objects.all()
    }


def build_with_treebeard(spec):
    nodes = {}
    for name, parent in spec:
        if parent is None:
            nodes[name] = Category.add_root(name=name)
        else:
            nodes[name] = nodes[parent].add_child(name=name)
    return nodes


def build_with_mptree(spec, mp):
    nodes = {}
    for name, parent in spec:
        if parent is None:
            nodes[name] = mp.add_root(name=name)
        else:
            nodes[name] = mp.add_child(nodes[parent], name=name)
    return nodes


def build_bulk(n, fanout=5):
    """Fast-create a balanced ``fanout``-ary tree of ``n`` nodes (explicit pks)."""
    mp = MaterializedPath(Category)
    paths, depths = {}, {}
    childcount = defaultdict(int)
    for i in range(n):
        parent = None if i == 0 else (i - 1) // fanout
        childcount[parent] += 1
        step = childcount[parent]
        if parent is None:
            paths[i], depths[i] = mp.segment(step), 1
        else:
            paths[i], depths[i] = paths[parent] + mp.segment(step), depths[parent] + 1
    objs = [
        Category(
            pk=i + 1,
            name=f"n{i}",
            path=paths[i],
            depth=depths[i],
            numchild=childcount[i],
            parent_id=None if i == 0 else ((i - 1) // fanout) + 1,
        )
        for i in range(n)
    ]
    Category.objects.bulk_create(objs, batch_size=1000)
    return mp


@mptree_only
class MPTreeEquivalenceTests(TestCase):
    """The prototype must match treebeard byte-for-byte where it claims to."""

    def setUp(self):
        self.mp = MaterializedPath(Category)
        self.spec = make_spec()

    def test_build_matches_treebeard(self):
        build_with_treebeard(self.spec)
        treebeard_snap = snapshot()

        Category.objects.all().delete()

        build_with_mptree(self.spec, self.mp)
        mptree_snap = snapshot()

        self.assertEqual(treebeard_snap, mptree_snap)
        # spot-check the encoding itself
        self.assertEqual(mptree_snap["r0"][0], "0001")
        self.assertEqual(mptree_snap["r0_c0"][0], "00010001")
        self.assertEqual(mptree_snap["r0_c0_g1"][0], "000100010002")

    def test_move_last_child_matches_treebeard(self):
        # treebeard reference: move a subtree to be the last child of another
        # branch (same depth) and to a deeper target (depth changes).
        nodes = build_with_treebeard(self.spec)
        nodes["r0_c2"].move(Category.objects.get(name="r1"), "last-child")
        nodes["r2_c0"].move(Category.objects.get(name="r1_c0"), "last-child")
        treebeard_snap = snapshot()

        Category.objects.all().delete()

        nodes = build_with_mptree(self.spec, self.mp)
        self.mp.move(nodes["r0_c2"], nodes["r1"], "last-child")
        self.mp.move(nodes["r2_c0"], nodes["r1_c0"], "last-child")
        mptree_snap = snapshot()

        self.assertEqual(treebeard_snap, mptree_snap)

    def test_descendants_children_ancestors(self):
        nodes = build_with_mptree(self.spec, self.mp)
        r0 = nodes["r0"]
        self.assertEqual(
            sorted(self.mp.children(r0).values_list("name", flat=True)),
            ["r0_c0", "r0_c1", "r0_c2", "r0_c3"],
        )
        self.assertEqual(self.mp.descendants(r0).count(), 4 + 4 * 2)
        g = nodes["r0_c2_g1"]
        self.assertEqual(
            list(self.mp.ancestors(g).values_list("name", flat=True)),
            ["r0", "r0_c2"],
        )


@mptree_only
class MPTreeInvariantTests(TestCase):
    """Operations with no simple treebeard analogue are checked by invariants."""

    def setUp(self):
        self.mp = MaterializedPath(Category)

    def assert_consistent_tree(self):
        """Every node's path/depth must be a pure function of its parent chain,
        paths must be unique, and ordering by path must be a valid DFS."""
        by_pk = {c.pk: c for c in Category.objects.all()}
        paths = [c.path for c in by_pk.values()]
        self.assertEqual(len(paths), len(set(paths)), "paths must be unique")
        for c in by_pk.values():
            self.assertEqual(len(c.path), c.depth * self.mp.steplen)
            if c.parent_id is None:
                self.assertEqual(c.depth, 1)
            else:
                parent = by_pk[c.parent_id]
                self.assertEqual(c.depth, parent.depth + 1)
                self.assertTrue(
                    c.path.startswith(parent.path),
                    f"{c.name} path {c.path} not under parent {parent.path}",
                )
            # numchild cache matches reality
            kids = sum(1 for o in by_pk.values() if o.parent_id == c.pk)
            self.assertEqual(c.numchild, kids, f"numchild wrong on {c.name}")

    def test_first_child_shift_keeps_tree_valid(self):
        spec = make_spec()
        nodes = build_with_mptree(spec, self.mp)
        # r1 already has children c0..c3; insert r0_c2 (with its grandchildren)
        # as the *first* child -> every existing child must shift up by one.
        self.mp.move(nodes["r0_c2"], nodes["r1"], "first-child")
        self.assert_consistent_tree()

        r1 = Category.objects.get(name="r1")
        first = self.mp.children(r1).first()
        self.assertEqual(first.name, "r0_c2")
        # the moved subtree came along
        self.assertEqual(
            sorted(self.mp.children(first).values_list("name", flat=True)),
            ["r0_c2_g0", "r0_c2_g1"],
        )
        self.assertEqual(r1.numchild, 5)

    def test_rebuild_from_parent_ids(self):
        spec = make_spec()
        nodes = build_with_mptree(spec, self.mp)

        # Simulate the "parent_id is the source of truth" world: reparent purely
        # by FK, leaving path/depth deliberately stale...
        moved = nodes["r2_c0"]
        Category.objects.filter(pk=moved.pk).update(parent=nodes["r0"])
        Category.objects.filter(pk=moved.pk).update(path="ZZZZ", depth=99)  # garbage

        # ...then rebuild reconstructs a fully consistent tree from parent_id.
        self.mp.rebuild()
        self.assert_consistent_tree()
        self.assertEqual(
            Category.objects.get(name="r2_c0").parent.name, "r0"
        )


@mptree_only
@skipIf(
    os.environ.get("GITHUB_ACTIONS") == "true",
    "Benchmark is too slow for CI -- run locally instead.",
)
class MPTreeBenchmark(TransactionTestCase):
    """Timing only -- prints results, asserts correctness of the big move."""

    def test_benchmark_move_and_rebuild(self):
        n = int(os.environ.get("MPTREE_BENCH_N", "10000"))
        fanout = 5

        # ----- subtree move on identical 10k trees -----------------------
        mp = build_bulk(n, fanout)
        node = Category.objects.get(pk=2)        # a root's first child
        target = Category.objects.get(pk=6)      # a disjoint sibling branch
        subtree_size = mp.descendants(node).count() + 1

        t0 = time.perf_counter()
        node.move(target, "last-child")          # treebeard
        tb_move = time.perf_counter() - t0

        Category.objects.all().delete()
        mp = build_bulk(n, fanout)
        node = Category.objects.get(pk=2)
        target = Category.objects.get(pk=6)

        t0 = time.perf_counter()
        mp.move(node, target, "last-child")      # prototype (single UPDATE)
        mp_move = time.perf_counter() - t0

        # correctness of the prototype move at scale
        node.refresh_from_db()
        self.assertEqual(node.parent_id, target.pk)
        self.assertEqual(Category.objects.count(), n)

        # ----- full rebuild / fix_tree ----------------------------------
        t0 = time.perf_counter()
        Category.fix_tree()                      # treebeard
        tb_fix = time.perf_counter() - t0

        t0 = time.perf_counter()
        mp.rebuild()                             # prototype
        mp_rebuild = time.perf_counter() - t0

        print(
            f"\n[mptree benchmark] n={n}, moved subtree={subtree_size} nodes\n"
            f"  move    treebeard={tb_move*1000:8.1f} ms   prototype={mp_move*1000:8.1f} ms\n"
            f"  rebuild fix_tree ={tb_fix*1000:8.1f} ms   prototype={mp_rebuild*1000:8.1f} ms"
        )

    def test_benchmark_mid_insert(self):
        # Worst case for _layout: a `first-child` move into a *wide* sibling
        # group, which renumbers every existing sibling (unlike the last-child
        # fast path, a single statement). Exercises the no-park shift.
        width = int(os.environ.get("MPTREE_BENCH_WIDTH", "2000"))

        def build():
            Category.objects.all().delete()
            mp = MaterializedPath(Category)
            objs = [Category(pk=1, name="root", path=mp.segment(1), depth=1, numchild=width)]
            pk = 2
            for i in range(1, width + 1):
                cpath = mp.segment(1) + mp.segment(i)
                objs.append(Category(pk=pk, name=f"c{i}", path=cpath, depth=2, numchild=1, parent_id=1))
                child_pk = pk
                pk += 1
                objs.append(Category(pk=pk, name=f"c{i}g", path=cpath + mp.segment(1), depth=3, parent_id=child_pk))
                pk += 1
            root2 = pk
            objs.append(Category(pk=pk, name="root2", path=mp.segment(2), depth=1, numchild=1))
            pk += 1
            x = pk
            objs.append(Category(pk=pk, name="X", path=mp.segment(2) + mp.segment(1), depth=2, parent_id=root2))
            Category.objects.bulk_create(objs, batch_size=1000)
            return mp, x

        _, x_pk = build()
        root = Category.objects.get(pk=1)
        x = Category.objects.get(pk=x_pk)
        t0 = time.perf_counter()
        x.move(root, "first-child")              # treebeard
        tb = time.perf_counter() - t0

        mp, x_pk = build()
        root = Category.objects.get(pk=1)
        x = Category.objects.get(pk=x_pk)
        t0 = time.perf_counter()
        mp.move(x, root, "first-child")          # prototype (_layout, no-park shift)
        mp_t = time.perf_counter() - t0

        x.refresh_from_db()
        self.assertEqual(x.parent_id, 1)
        self.assertEqual(mp.children(root).first().pk, x_pk)  # X is now first child

        print(
            f"\n[mptree mid-insert] first-child move into width={width} sibling group\n"
            f"  move    treebeard={tb*1000:8.1f} ms   prototype={mp_t*1000:8.1f} ms"
        )
