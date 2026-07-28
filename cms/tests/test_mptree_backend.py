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

from unittest import skipUnless

from django.test import SimpleTestCase
from treebeard.mp_tree import MP_Node

from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mptree import MaterializedPathMixin, get_tree_backend, get_tree_base

TEMPLATE = "nav_playground.html"

mptree_only = skipUnless(
    get_tree_backend() == "mptree",
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
