"""
Guardrail + functional tests for the swappable tree backend.

* ``TreeFieldParityTests`` proves the swap is *migration-invisible*: Django
  builds migrations purely from field deconstruction, so if
  ``MaterializedPathMixin`` deconstructs its tree fields identically to
  treebeard's ``MP_Node``, substituting one for the other produces no migration.

* ``PageTreeBackendTests`` are ordinary page-tree tests that run under
  *whichever* backend the process booted with. Running this module twice --

      python manage.py test cms.tests.test_mptree_backend
      CMS_TREE_BACKEND=mptree python manage.py test cms.tests.test_mptree_backend

  and getting green both times is the behavioural-parity proof for what they
  cover (build, query, move).
"""

from django.test import SimpleTestCase
from treebeard.mp_tree import MP_Node

from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase
from cms.utils.mptree import MaterializedPathMixin, get_tree_base

TEMPLATE = "nav_playground.html"


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
        import os

        expected = (
            MaterializedPathMixin
            if os.environ.get("CMS_TREE_BACKEND") == "mptree"
            else MP_Node
        )
        self.assertIs(get_tree_base(), expected)

    def test_queryset_is_treebeard_free_in_mptree_mode(self):
        # The page queryset must not inherit from treebeard when the mptree
        # backend is active -- otherwise treebeard would be imported.
        import os

        from cms.models.query import PageQuerySet

        mro_modules = {base.__module__ for base in PageQuerySet.__mro__}
        if os.environ.get("CMS_TREE_BACKEND") == "mptree":
            self.assertNotIn("treebeard.mp_tree", mro_modules)
        else:
            self.assertIn("treebeard.mp_tree", mro_modules)
        # The manager is backend-agnostic (never treebeard) in either mode.
        from cms.models import Page

        self.assertNotIn("treebeard", type(Page.objects).__module__)


class PageTreeBackendTests(CMSTestCase):
    """Runs under the active backend; identical assertions must hold for both."""

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
