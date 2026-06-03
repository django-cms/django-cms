"""
Prototype validation for cms.utils.mptree (dependency-free materialized path).

Two things are proven here:

1. **Equivalence to treebeard** -- building a tree and doing a ``last-child``
   move through the prototype produces byte-for-byte identical
   ``path``/``depth``/``numchild`` to django-treebeard's ``MP_Node`` (validated
   against the existing ``Category`` test model, which *is* an ``MP_Node``).
   This means an in-place migration would not have to rewrite ``path`` values.

2. **Correctness + scale** -- invariant checks for the trickier operations
   (first-child insert with sibling shift, full rebuild from ``parent_id``), and
   a 10k-node benchmark timing a subtree move and a rebuild against treebeard.

Run just this module::

    python manage.py test cms.tests.test_mptree_prototype

The benchmark prints timings; set ``MPTREE_BENCH_N`` to change the node count
(default 10000).
"""

import os
import time
from collections import defaultdict

from django.test import TestCase, TransactionTestCase

from cms.test_utils.project.sampleapp.models import Category
from cms.utils.mptree import MaterializedPath


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
