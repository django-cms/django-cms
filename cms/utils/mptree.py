"""
Dependency-free materialized-path tree backend (experimental).

This explores replacing the ``django-treebeard`` dependency for the page tree
by treating ``parent_id`` as the single source of truth and maintaining
``path``/``depth``/``numchild`` as a derived, set-based-recomputed cache.

The module ships three things:

* :class:`MaterializedPath` -- a low-level *driver* implementing the tree
  algorithms against any model exposing the treebeard column layout
  (``path``/``depth``/``numchild``/``parent``). Operates set-based, never pulls
  a subtree into Python on the hot paths, uses only cross-database ORM
  functions (``Concat``/``Substr``/``Length``/``F``), and locks at *parent-row*
  granularity for concurrency.
* :class:`MaterializedPathMixin` -- an abstract model exposing the subset of the
  treebeard ``MP_Node`` API that django-cms uses, delegating to the driver. Its
  fields are declared **identically to treebeard** so that swapping it in for
  ``MP_Node`` produces *no* migration.
* :func:`get_tree_base` -- selects the base class (treebeard or this) from the
  ``CMS_TREE_BACKEND`` setting, so the backend can be swapped per-deployment
  (setting + restart, same database, no migration).

The path encoding is byte-for-byte compatible with treebeard's defaults
(base-36 alphabet, ``steplen=4``, no separators), so existing ``path`` values
remain valid in either direction.
"""

from collections import defaultdict

from django.db import models, transaction
from django.db.models import F, Value
from django.db.models.functions import Concat, Substr

DEFAULT_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_STEPLEN = 4


class MaterializedPath:
    """
    Set-based materialized-path operations for a model with the treebeard
    column layout: ``path`` (unique CharField), ``depth``, ``numchild`` and a
    self-referential ``parent`` FK.

    ``scope`` is an optional dict of field lookups that partitions the forest
    (e.g. ``{"site_id": 3}``). It defaults to no scope, i.e. the whole table is
    one forest -- matching treebeard's behaviour for the page tree.
    """

    def __init__(self, model, *, steplen=DEFAULT_STEPLEN, alphabet=DEFAULT_ALPHABET, scope=None, lock=True):
        self.model = model
        self.steplen = steplen
        self.alphabet = alphabet
        self.radix = len(alphabet)
        self.scope = scope or {}
        self.lock = lock

    # -- encoding (treebeard-compatible) ---------------------------------

    def _int2str(self, num):
        ret = ""
        num = int(num)
        while True:
            ret = self.alphabet[num % self.radix] + ret
            if num < self.radix:
                return ret
            num //= self.radix

    def _str2int(self, key):
        num = 0
        for char in key:
            num = num * self.radix + self.alphabet.index(char)
        return num

    def segment(self, step):
        """The fixed-width path segment for a 1-based sibling ``step``."""
        key = self._int2str(step)
        return self.alphabet[0] * (self.steplen - len(key)) + key

    def step_of(self, path):
        """Decode the last (own) segment of ``path`` back to its integer step."""
        return self._str2int(path[-self.steplen :])

    # -- read queries ----------------------------------------------------

    def _scoped(self):
        return self.model._default_manager.filter(**self.scope)

    def roots(self):
        return self._scoped().filter(depth=1).order_by("path")

    def children(self, node):
        return self._scoped().filter(
            path__startswith=node.path, depth=node.depth + 1
        ).order_by("path")

    def descendants(self, node):
        # The materialized path *is* the precomputed recursion: an indexed
        # prefix scan, no WITH RECURSIVE required.
        return self._scoped().filter(
            path__startswith=node.path, depth__gt=node.depth
        ).order_by("path")

    def ancestors(self, node):
        paths = [
            node.path[0:pos]
            for pos in range(self.steplen, len(node.path), self.steplen)
        ]
        if not paths:
            return self.model._default_manager.none()
        return self._scoped().filter(path__in=paths).order_by("path")

    def tree(self, parent=None):
        if parent is None:
            return self._scoped().order_by("path")
        return self._scoped().filter(
            path__startswith=parent.path, depth__gte=parent.depth
        ).order_by("path")

    def root_of(self, node):
        return self._scoped().get(path=node.path[0 : self.steplen])

    def _children_rows(self, parent_path, parent_depth):
        # Ordered direct children as lightweight (deferred) instances, fetched
        # once and reused for index/append/layout to avoid repeat queries.
        return list(
            self._scoped()
            .filter(path__startswith=parent_path, depth=parent_depth + 1)
            .order_by("path")
            .only("pk", "path", "depth")
        )

    def _ordered_child_pks(self, parent_path, parent_depth):
        return [c.pk for c in self._children_rows(parent_path, parent_depth)]

    def _last_child_step(self, parent_path, parent_depth, exclude_pk=None):
        qs = self._scoped().filter(path__startswith=parent_path, depth=parent_depth + 1)
        if exclude_pk is not None:
            # When *moving* a node to the end of its own sibling group, its
            # current slot must not count -- otherwise it would be bumped into a
            # spurious gap instead of staying put.
            qs = qs.exclude(pk=exclude_pk)
        last = qs.order_by("path").values_list("path", flat=True).last()
        return self.step_of(last) if last else 0

    def _last_root_step(self):
        last = self.roots().values_list("path", flat=True).last()
        return self.step_of(last) if last else 0

    # -- concurrency -----------------------------------------------------

    def _lock_rows(self, *pks):
        """
        Take row-level write locks (in pk order, to avoid deadlocks) on the rows
        whose sibling slot / numchild caches an operation will touch. Parent-row
        granularity: writes under different parents do not serialise against each
        other. No-op on backends without ``SELECT ... FOR UPDATE`` (SQLite).
        """
        if not self.lock:
            return
        pks = sorted({pk for pk in pks if pk is not None})
        if pks:
            list(
                self.model._base_manager.filter(pk__in=pks)
                .order_by("pk")
                .select_for_update()
            )

    # -- low-level subtree rewrite --------------------------------------

    def _reprefix(self, *, old_prefix, new_prefix, depth_delta):
        """
        Rewrite an entire subtree's paths by prefix-swap in one statement::

            new path = new_prefix || (old path with its old_prefix stripped)

        Never pulls descendant rows into Python.
        """
        qs = self._scoped().filter(path__startswith=old_prefix)
        update = {"path": Concat(Value(new_prefix), Substr("path", len(old_prefix) + 1))}
        if depth_delta:
            update["depth"] = F("depth") + depth_delta
        qs.update(**update)

    def _layout(self, parent_path, parent_depth, ordered_pks, info=None):
        """
        Lay the given child subtrees out as contiguous steps ``1..n`` under the
        parent, in the given order, fixing each subtree's prefix *and* depth.
        ``info`` may carry already-fetched ``{pk: instance}`` rows (with
        ``path``/``depth``) so the caller's prior query can be reused.

        Two correctness-preserving shortcuts, both byte-identical to a naive
        full relayout:

        * **Skip already-placed children.** Target slots are a permutation of
          ``1..n``, so a child already at its target slot is wanted by no other
          child -- leaving it can never collide. Turns "insert near the end"
          from O(n) rewrites into O(moved).
        * **Skip the parking pass when nothing moves *down*.** Parking into the
          disjoint ``~<pk>~`` namespace only exists to break collisions. If no
          mover targets a lower slot than it currently holds (the usual
          insert/shift-up / move-from-elsewhere case), writing movers
          highest-slot-first always lands in a slot just vacated (or never
          occupied), so a single pass suffices -- halving the statements.
          A genuine down-move (e.g. moving a later sibling to an earlier slot)
          falls back to the always-safe park-then-write.
        """
        known = dict(info or {})
        missing = [pk for pk in ordered_pks if pk not in known]
        if missing:
            for obj in self._scoped().filter(pk__in=missing).only("pk", "path", "depth"):
                known[obj.pk] = obj

        target_depth = parent_depth + 1
        prefix_len = len(parent_path)
        movers = []  # (pk, target_step, target_prefix, old_path, depth_delta, old_slot)
        for step, pk in enumerate(ordered_pks, start=1):
            obj = known[pk]
            target_prefix = parent_path + self.segment(step)
            if obj.path == target_prefix and obj.depth == target_depth:
                continue  # already in place; cannot collide (slots are unique)
            is_child_here = (
                obj.depth == target_depth
                and obj.path.startswith(parent_path)
                and len(obj.path) == prefix_len + self.steplen
            )
            old_slot = self.step_of(obj.path) if is_child_here else None
            movers.append((pk, step, target_prefix, obj.path, target_depth - obj.depth, old_slot))

        needs_park = any(slot is not None and step < slot for _, step, _, _, _, slot in movers)
        if needs_park:
            for pk, _, _, old_path, _, _ in movers:
                self._reprefix(old_prefix=old_path, new_prefix=f"~{pk}~", depth_delta=0)
            for pk, _, target_prefix, _, depth_delta, _ in movers:
                self._reprefix(old_prefix=f"~{pk}~", new_prefix=target_prefix, depth_delta=depth_delta)
        else:
            # highest target slot first -> destination is always free
            for pk, _, target_prefix, old_path, depth_delta, _ in sorted(
                movers, key=lambda m: m[1], reverse=True
            ):
                self._reprefix(old_prefix=old_path, new_prefix=target_prefix, depth_delta=depth_delta)

    # -- node construction ----------------------------------------------

    def _materialise(self, instance, attrs, *, path, depth, parent):
        # `parent`/`parent_id` are determined by the tree operation, not by the
        # caller's kwargs (treebeard's add_child/add_sibling accept them as
        # redundant field values) -- drop them so they can't conflict.
        attrs.pop("parent", None)
        attrs.pop("parent_id", None)
        if instance is None:
            instance = self.model(**{**self.scope, **attrs})
        instance.path = path
        instance.depth = depth
        instance.numchild = 0
        instance.parent = parent
        for field, value in self.scope.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    @staticmethod
    def _bump_numchild(model, pk, delta):
        if pk is not None:
            model._base_manager.filter(pk=pk).update(numchild=F("numchild") + delta)

    # -- build (append + positional insert) ------------------------------

    @transaction.atomic
    def add_root(self, instance=None, **attrs):
        self._lock_rows(*self.roots().values_list("pk", flat=True))
        step = self._last_root_step() + 1
        return self._materialise(
            instance, attrs, path=self.segment(step), depth=1, parent=None
        )

    @transaction.atomic
    def add_child(self, parent, position="last-child", instance=None, **attrs):
        self._lock_rows(parent.pk)
        step = self._last_child_step(parent.path, parent.depth) + 1
        node = self._materialise(
            instance,
            attrs,
            path=parent.path + self.segment(step),
            depth=parent.depth + 1,
            parent=parent,
        )
        self._bump_numchild(self.model, parent.pk, +1)
        parent.numchild = (parent.numchild or 0) + 1  # keep caller's instance honest
        if position == "first-child":
            existing = [pk for pk in self._ordered_child_pks(parent.path, parent.depth) if pk != node.pk]
            self._layout(parent.path, parent.depth, [node.pk] + existing)
            node.refresh_from_db()
        return node

    @transaction.atomic
    def add_sibling(self, node, position="last-sibling", instance=None, **attrs):
        parent = node.parent
        if parent is None:
            new = self.add_root(instance=instance, **attrs)
            if position in ("first-sibling", "left"):
                # rare: reorder roots is not exercised by django-cms; left to
                # rebuild() which canonicalises root order.
                pass
            return new
        new = self.add_child(parent, instance=instance, **attrs)
        if position in ("last-sibling", "right"):
            # 'right' relative to an arbitrary sibling still lands at the end in
            # this minimal implementation unless it must sit immediately after
            # `node`; place precisely:
            self._place_relative(new, node, after=(position == "right"))
        elif position in ("first-sibling", "left"):
            self._place_relative(new, node, after=False)
        return new

    def _place_relative(self, node, sibling, *, after):
        parent = sibling.parent
        parent_path = parent.path if parent else ""
        parent_depth = parent.depth if parent else 0
        order = [pk for pk in self._ordered_child_pks(parent_path, parent_depth) if pk != node.pk]
        idx = order.index(sibling.pk) + (1 if after else 0)
        order.insert(idx, node.pk)
        self._layout(parent_path, parent_depth, order)
        node.refresh_from_db()

    # -- move (single statement for append; layout for insert) -----------

    @transaction.atomic
    def move(self, node, target, pos="last-child"):
        """
        Move ``node`` (and its whole subtree). Supported ``pos``:
        ``last-child``/``first-child`` (relative to ``target``) and
        ``left``/``right`` (relative to sibling ``target``).
        """
        old_parent_id = (
            self.model._base_manager.filter(pk=node.pk)
            .values_list("parent_id", flat=True)
            .first()
        )
        if pos in ("left", "right"):
            new_parent = target.parent
            self._lock_rows(node.pk, old_parent_id, new_parent.pk if new_parent else None)
        else:
            new_parent = target
            self._lock_rows(node.pk, old_parent_id, target.pk)

        node.refresh_from_db()
        target.refresh_from_db()
        if new_parent is not None:
            new_parent.refresh_from_db()

        if new_parent is not None and (
            target.path == node.path or new_parent.path.startswith(node.path)
        ):
            raise ValueError("Cannot move a node into itself or its own subtree.")

        parent_path = new_parent.path if new_parent else ""
        parent_depth = new_parent.depth if new_parent else 0

        if pos == "last-child":
            # Fast path: a single set-based UPDATE, no sibling touched.
            new_step = self._last_child_step(parent_path, parent_depth, exclude_pk=node.pk) + 1
            new_prefix = parent_path + self.segment(new_step)
            depth_delta = (parent_depth + 1) - node.depth
            self._reprefix(old_prefix=node.path, new_prefix=new_prefix, depth_delta=depth_delta)
        else:
            # One child fetch, reused for index lookup, append step and layout.
            siblings = [c for c in self._children_rows(parent_path, parent_depth) if c.pk != node.pk]
            order = [c.pk for c in siblings]
            if pos == "first-child":
                idx = 0
            elif pos == "left":
                idx = order.index(target.pk)
            else:  # right
                idx = order.index(target.pk) + 1
            if idx == len(order):
                # Landing at the end is an append: one set-based UPDATE, leaving
                # the vacated source slot as a gap (matching treebeard, and far
                # cheaper than relaying out every sibling).
                new_step = (self.step_of(siblings[-1].path) + 1) if siblings else 1
                new_prefix = parent_path + self.segment(new_step)
                depth_delta = (parent_depth + 1) - node.depth
                self._reprefix(old_prefix=node.path, new_prefix=new_prefix, depth_delta=depth_delta)
            else:
                order.insert(idx, node.pk)
                # node carries fresh path/depth; pass everything so _layout needs
                # no further query.
                info = {c.pk: c for c in siblings}
                info[node.pk] = node
                self._layout(parent_path, parent_depth, order, info=info)

        new_parent_pk = new_parent.pk if new_parent else None
        self.model._base_manager.filter(pk=node.pk).update(parent=new_parent)
        if old_parent_id != new_parent_pk:
            self._bump_numchild(self.model, old_parent_id, -1)
            self._bump_numchild(self.model, new_parent_pk, +1)
        # Keep the caller's in-memory instances honest: `node` moved, and
        # `target` may have been renumbered (left/right) or had its numchild
        # change (first/last-child) -- treebeard updates these in place too.
        node.refresh_from_db()
        target.refresh_from_db()

    # -- rebuild (recompute everything from parent_id) -------------------

    @transaction.atomic
    def rebuild(self):
        """
        Recompute every ``path``/``depth``/``numchild`` in the scope from the
        tree structure, compacting sibling steps to ``1..N`` while **preserving
        the existing sibling order** (read from the current ``path``, exactly
        like treebeard's ``fix_tree``). The dependency-free replacement for
        ``fix_tree`` -- a rare maintenance operation, written back in two
        collision-free passes (park in the disjoint ``~<pk>`` namespace, then
        write final values).

        Ordering by ``path`` means siblings keep the order an editor arranged,
        not creation order -- so no separate ``position`` field is needed for
        order to survive a rebuild.
        """
        rows = list(
            self._scoped().order_by("path").values("pk", "parent_id")
        )
        present = {r["pk"] for r in rows}
        children = defaultdict(list)
        for r in rows:
            # rows are in path order, so each parent's children list is built in
            # sibling order
            parent = r["parent_id"] if r["parent_id"] in present else None
            children[parent].append(r["pk"])

        computed = {}
        stack = [(None, "", 1)]
        while stack:
            parent_pk, parent_path, depth = stack.pop()
            for step, pk in enumerate(children.get(parent_pk, []), start=1):
                path = parent_path + self.segment(step)
                computed[pk] = [path, depth, len(children.get(pk, []))]
                stack.append((pk, path, depth + 1))

        self.model._base_manager.bulk_update(
            [self.model(pk=pk, path=f"~{pk}") for pk in computed],
            ["path"],
            batch_size=500,
        )
        self.model._base_manager.bulk_update(
            [
                self.model(pk=pk, path=p, depth=d, numchild=n)
                for pk, (p, d, n) in computed.items()
            ],
            ["path", "depth", "numchild"],
            batch_size=500,
        )
        return len(computed)


class MaterializedPathMixin(models.Model):
    """
    Drop-in replacement base for treebeard's ``MP_Node`` covering the API that
    django-cms uses. Fields are declared **identically to treebeard** so that
    substituting this for ``MP_Node`` generates no migration.
    """

    path = models.CharField(max_length=255, unique=True)
    depth = models.PositiveIntegerField()
    numchild = models.PositiveIntegerField(default=0)

    steplen = DEFAULT_STEPLEN
    alphabet = DEFAULT_ALPHABET
    node_order_by = []

    class Meta:
        abstract = True

    # -- driver ----------------------------------------------------------

    @classmethod
    def _tree(cls):
        return MaterializedPath(cls, steplen=cls.steplen, alphabet=cls.alphabet)

    # -- treebeard-compatible API ---------------------------------------

    @classmethod
    def add_root(cls, instance=None, **attrs):
        return cls._tree().add_root(instance=instance, **attrs)

    @classmethod
    def get_root_nodes(cls):
        return cls._tree().roots()

    @classmethod
    def get_tree(cls, parent=None):
        return cls._tree().tree(parent)

    @classmethod
    def fix_tree(cls, **kwargs):
        return cls._tree().rebuild()

    def add_child(self, instance=None, **attrs):
        attrs.pop("parent", None)  # redundant: the parent is `self`
        return self._tree().add_child(self, instance=instance, **attrs)

    def add_sibling(self, pos="last-sibling", instance=None, **attrs):
        attrs.pop("parent", None)
        attrs.pop("parent_id", None)
        return self._tree().add_sibling(self, position=pos, instance=instance, **attrs)

    def move(self, target, pos="last-child"):
        self._tree().move(self, target, pos)

    def get_children(self):
        return self._tree().children(self)

    def get_descendants(self):
        return self._tree().descendants(self)

    def get_ancestors(self):
        return self._tree().ancestors(self)

    def get_root(self):
        return self._tree().root_of(self)

    def get_parent(self, update=False):
        return self.parent

    def get_first_child(self):
        return self._tree().children(self).first()

    def is_root(self):
        return self.depth == 1

    def is_leaf(self):
        return self.numchild == 0

    def is_sibling_of(self, other):
        return self.depth == other.depth and self.parent_id == other.parent_id

    def is_child_of(self, other):
        return self.parent_id == other.pk

    def is_descendant_of(self, other):
        return self.depth > other.depth and self.path.startswith(other.path)

    def get_siblings(self):
        if self.parent_id is None:
            return self._tree().roots()
        return self._tree().children(self.parent)

    def delete(self, *args, **kwargs):
        # Deleting a node removes it from its parent's child set; keep the
        # parent's numchild cache correct (treebeard does this via its
        # queryset/model delete overrides). Descendants are removed by the
        # parent FK's on_delete cascade and do not affect surviving nodes.
        parent_id = self.parent_id
        result = super().delete(*args, **kwargs)
        if parent_id is not None:
            type(self)._base_manager.filter(pk=parent_id).update(
                numchild=models.F("numchild") - 1
            )
        return result


def get_tree_base():
    """
    Return the base class for the page tree, chosen by the ``CMS_TREE_BACKEND``
    setting (``"treebeard"`` -- the default -- or ``"mptree"``).

    An env var of the same name overrides the setting only when the setting is
    not explicitly defined; this keeps the byte-for-byte-compatible backends
    swappable in CI / subprocess tests without touching the settings module.
    Selection happens at import time, so a change requires a process restart --
    but no database migration, because both backends declare identical fields.
    """
    import os

    from django.conf import settings

    backend = getattr(settings, "CMS_TREE_BACKEND", None) or os.environ.get(
        "CMS_TREE_BACKEND", "treebeard"
    )
    if backend == "mptree":
        return MaterializedPathMixin

    from treebeard.mp_tree import MP_Node

    return MP_Node
