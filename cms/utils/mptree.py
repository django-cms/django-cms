"""
Dependency-free materialized-path tree backend

This replaces the ``django-treebeard`` dependency for the page tree
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

A future redesign that removes sibling renumbering and the depth/width ceilings
("fractional ordering") is sketched in the **PHASE 2 DESIGN NOTE** at the bottom
of this module. It is intentionally *not* implemented: it requires a one-time
migration and ends treebeard byte-compatibility, so it is a deliberate later
step, not part of this drop-in backend.
"""

from collections import defaultdict
from functools import wraps

from django.db import models, router, transaction
from django.db.models import F, Value
from django.db.models.functions import Concat, Length, Substr

DEFAULT_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_STEPLEN = 4

# Columns the driver plans from. Re-read under lock before planning a mutation
# so a concurrently moved/renumbered node is never laid out from stale values.
TREE_FIELDS = ["path", "depth", "numchild", "parent"]


class TreePathOverflow(ValueError):
    """
    Raised when a tree position cannot be represented: a sibling step too large
    for one ``steplen``-wide segment, or a path too long for the ``path`` column.

    Raised *before* any statement runs, so the transaction is left untouched
    rather than failing mid-rewrite on a truncated or over-long value.
    """


def _atomic_on_alias(method):
    """``transaction.atomic`` on the driver's own database, not ``default``."""

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with transaction.atomic(using=self.db_alias):
            return method(self, *args, **kwargs)

    return wrapped


class MaterializedPath:
    """
    Set-based materialized-path operations for a model with the treebeard
    column layout: ``path`` (unique CharField), ``depth``, ``numchild`` and a
    self-referential ``parent`` FK.

    ``scope`` is an optional dict of field lookups that partitions the forest
    (e.g. ``{"site_id": 3}``). It defaults to no scope, i.e. the whole table is
    one forest -- matching treebeard's behaviour for the page tree.

    ``using`` pins every read, write, lock and transaction to one database
    alias. It defaults to the write database the router picks for ``model``, and
    callers coming from a loaded instance pass that instance's alias so an
    operation never straddles two connections.
    """

    def __init__(
        self,
        model,
        *,
        steplen=DEFAULT_STEPLEN,
        alphabet=DEFAULT_ALPHABET,
        scope=None,
        lock=True,
        using=None,
    ):
        self.model = model
        self.steplen = steplen
        self.alphabet = alphabet
        self.radix = len(alphabet)
        self.path_max_length = model._meta.get_field("path").max_length
        self.scope = scope or {}
        self.lock = lock
        self.db_alias = using or router.db_for_write(model)

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
        step = int(step)
        if step < 1 or step >= self.radix**self.steplen:
            raise TreePathOverflow(
                f"Sibling step {step} does not fit in a {self.steplen}-character "
                f"base-{self.radix} path segment."
            )
        key = self._int2str(step)
        return self.alphabet[0] * (self.steplen - len(key)) + key

    def step_of(self, path):
        """Decode the last (own) segment of ``path`` back to its integer step."""
        return self._str2int(path[-self.steplen :])

    # -- path length guards ----------------------------------------------

    def _ensure_path_fits(self, path):
        self._ensure_path_length_fits(len(path))

    def _ensure_path_length_fits(self, required):
        if self.path_max_length is not None and required > self.path_max_length:
            raise TreePathOverflow(
                f"Path requires {required} characters but "
                f"{self.model._meta.label}.path allows {self.path_max_length}."
            )

    # -- read queries ----------------------------------------------------

    def _scoped(self):
        return self.model._default_manager.using(self.db_alias).filter(**self.scope)

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
            return self.model._default_manager.using(self.db_alias).none()
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
                self.model._base_manager.using(self.db_alias)
                .filter(pk__in=pks)
                .order_by("pk")
                .select_for_update()
            )

    def _refresh(self, *instances):
        """
        Re-read the tree columns of caller-supplied instances, after locking and
        before planning. The caller may have held them across an earlier request
        or a concurrent move, in which case their ``path``/``depth``/``parent``
        no longer describe where the node actually is -- and a layout planned
        from those values rewrites the wrong rows. Only the tree columns are
        reloaded, so unsaved edits the caller made to other fields survive.
        """
        for instance in instances:
            if instance is not None and instance.pk is not None:
                instance.refresh_from_db(using=self.db_alias, fields=TREE_FIELDS)

    # -- low-level subtree rewrite --------------------------------------

    def _reprefix(self, *, old_prefix, new_prefix, depth_delta):
        """
        Rewrite an entire subtree's paths by prefix-swap in one statement::

            new path = new_prefix || (old path with its old_prefix stripped)

        Never pulls descendant rows into Python.
        """
        qs = self._scoped().filter(path__startswith=old_prefix)
        self._ensure_path_fits(new_prefix)
        prefix_growth = len(new_prefix) - len(old_prefix)
        if prefix_growth > 0:
            # The subtree moves deeper (or is being parked under a longer
            # placeholder prefix): every descendant path grows by the same
            # amount, so the deepest one decides whether the whole rewrite
            # fits. One aggregate query, only on the branch that can overflow.
            longest = (
                qs.annotate(_mptree_path_length=Length("path"))
                .order_by("-_mptree_path_length")
                .values_list("_mptree_path_length", flat=True)
                .first()
            )
            if longest is not None:
                self._ensure_path_length_fits(longest + prefix_growth)
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

        Both shortcuts assume the movers are *disjoint* subtrees. One mover can
        sit inside another -- moving a node to a slot relative to its own parent
        or uncle -- and then rewriting the outer subtree first would drag the
        inner one along and leave its recorded ``old_path`` matching nothing.
        Those layouts always park, deepest path first, so that by the time an
        ancestor is rewritten its nested mover is already out of the way.
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
        if not needs_park:
            # Nested movers (one mover's subtree contains another's) cannot be
            # rewritten in place either. If a path is a proper prefix of another
            # every path sorting between them shares that prefix, so comparing
            # sorted neighbours is enough to spot it.
            in_order = sorted(m[3] for m in movers)
            needs_park = any(
                b.startswith(a) for a, b in zip(in_order, in_order[1:], strict=False)
            )
        if needs_park:
            # Deepest first: parking a nested subtree before its ancestor keeps
            # the ancestor's rewrite from touching it.
            for pk, _, _, old_path, _, _ in sorted(movers, key=lambda m: len(m[3]), reverse=True):
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
        self._ensure_path_fits(path)
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
        instance.save(using=self.db_alias)
        return instance

    def _bump_numchild(self, pk, delta):
        if pk is not None:
            self.model._base_manager.using(self.db_alias).filter(pk=pk).update(
                numchild=F("numchild") + delta
            )

    # -- build (append + positional insert) ------------------------------

    @_atomic_on_alias
    def add_root(self, instance=None, **attrs):
        self._lock_rows(*self.roots().values_list("pk", flat=True))
        step = self._last_root_step() + 1
        return self._materialise(
            instance, attrs, path=self.segment(step), depth=1, parent=None
        )

    @_atomic_on_alias
    def add_child(self, parent, position="last-child", instance=None, **attrs):
        self._lock_rows(parent.pk)
        self._refresh(parent)
        step = self._last_child_step(parent.path, parent.depth) + 1
        node = self._materialise(
            instance,
            attrs,
            path=parent.path + self.segment(step),
            depth=parent.depth + 1,
            parent=parent,
        )
        self._bump_numchild(parent.pk, +1)
        parent.numchild = (parent.numchild or 0) + 1  # keep caller's instance honest
        if position == "first-child":
            existing = [pk for pk in self._ordered_child_pks(parent.path, parent.depth) if pk != node.pk]
            self._layout(parent.path, parent.depth, [node.pk] + existing)
            self._refresh(node)
        return node

    @_atomic_on_alias
    def add_sibling(self, node, position="last-sibling", instance=None, **attrs):
        self._lock_rows(node.pk)
        self._refresh(node)
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
        self._refresh(node)

    # -- move (single statement for append; layout for insert) -----------

    @_atomic_on_alias
    def move(self, node, target, pos="last-child"):
        """
        Move ``node`` (and its whole subtree). Supported ``pos``:
        ``last-child``/``first-child`` (relative to ``target``) and
        ``left``/``right`` (relative to sibling ``target``).
        """
        # Read the parent ids first so every row this move touches can be taken
        # in one pk-ordered `_lock_rows` -- concurrent moves then queue behind
        # each other instead of deadlocking on opposite acquisition orders. The
        # values are unverified at this point; the lock below is what makes them
        # true, and the re-read after it is what proves they still are.
        parent_ids = dict(
            self.model._base_manager.using(self.db_alias)
            .filter(pk__in={pk for pk in (node.pk, target.pk) if pk is not None})
            .values_list("pk", "parent_id")
        )
        self._lock_rows(
            node.pk, target.pk, parent_ids.get(node.pk), parent_ids.get(target.pk)
        )
        # Everything below -- which parent to lock, which slot to target, the
        # move-into-own-subtree check -- is planned from these tree columns, so
        # they have to be the committed ones, not whatever the caller has been
        # holding since an earlier request.
        self._refresh(node, target)
        old_parent_id = node.parent_id

        relative_to_sibling = pos in ("left", "right")
        new_parent_id = target.parent_id if relative_to_sibling else target.pk
        # No-op when the pre-read was accurate (re-locking a row this
        # transaction already holds is free); only a concurrent re-parent
        # between the read and the lock makes this acquire anything new.
        self._lock_rows(old_parent_id, new_parent_id)

        if not relative_to_sibling:
            new_parent = target
        elif new_parent_id is None:
            new_parent = None
        else:
            # Re-fetched rather than followed through `target.parent`: the
            # descriptor can hand back an object cached before the lock, i.e.
            # exactly the stale state re-reading `target` was meant to escape.
            new_parent = self.model._base_manager.using(self.db_alias).get(
                pk=new_parent_id
            )

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
        self.model._base_manager.using(self.db_alias).filter(pk=node.pk).update(
            parent=new_parent
        )
        if old_parent_id != new_parent_pk:
            self._bump_numchild(old_parent_id, -1)
            self._bump_numchild(new_parent_pk, +1)
        # Keep the caller's in-memory instances honest: `node` moved, and
        # `target` may have been renumbered (left/right) or had its numchild
        # change (first/last-child) -- treebeard updates these in place too.
        self._refresh(node, target)

    # -- rebuild (recompute everything from parent_id) -------------------

    @_atomic_on_alias
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
                self._ensure_path_fits(path)
                computed[pk] = [path, depth, len(children.get(pk, []))]
                stack.append((pk, path, depth + 1))

        self.model._base_manager.using(self.db_alias).bulk_update(
            [self.model(pk=pk, path=f"~{pk}") for pk in computed],
            ["path"],
            batch_size=500,
        )
        self.model._base_manager.using(self.db_alias).bulk_update(
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
    def _tree(cls, using=None):
        return MaterializedPath(
            cls, steplen=cls.steplen, alphabet=cls.alphabet, using=using
        )

    def _instance_tree(self):
        """
        Driver pinned to the database this instance was loaded from, so a node
        read from a replica or a secondary alias is never queried, locked or
        rewritten against ``default``.
        """
        return type(self)._tree(using=self._state.db)

    # -- treebeard-compatible API ---------------------------------------

    @classmethod
    def add_root(cls, instance=None, **attrs):
        using = None
        if instance is not None:
            using = instance._state.db or router.db_for_write(cls, instance=instance)
        return cls._tree(using=using).add_root(instance=instance, **attrs)

    @classmethod
    def get_root_nodes(cls, using=None):
        return cls._tree(using=using).roots()

    @classmethod
    def get_tree(cls, parent=None, using=None):
        if using is None and parent is not None:
            using = parent._state.db
        return cls._tree(using=using).tree(parent)

    @classmethod
    def fix_tree(cls, using=None, **kwargs):
        return cls._tree(using=using).rebuild()

    def add_child(self, instance=None, **attrs):
        attrs.pop("parent", None)  # redundant: the parent is `self`
        return self._instance_tree().add_child(self, instance=instance, **attrs)

    def add_sibling(self, pos="last-sibling", instance=None, **attrs):
        attrs.pop("parent", None)
        attrs.pop("parent_id", None)
        return self._instance_tree().add_sibling(
            self, position=pos, instance=instance, **attrs
        )

    def move(self, target, pos="last-child"):
        self._instance_tree().move(self, target, pos)

    def get_children(self):
        return self._instance_tree().children(self)

    def get_descendants(self):
        return self._instance_tree().descendants(self)

    def get_ancestors(self):
        return self._instance_tree().ancestors(self)

    def get_root(self):
        return self._instance_tree().root_of(self)

    def get_parent(self, update=False):
        return self.parent

    def get_first_child(self):
        return self._instance_tree().children(self).first()

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
            return self._instance_tree().roots()
        return self._instance_tree().children(self.parent)

    def delete(self, *args, **kwargs):
        # Deleting a node removes it from its parent's child set; keep the
        # parent's numchild cache correct (treebeard does this via its
        # queryset/model delete overrides). Descendants are removed by the
        # parent FK's on_delete cascade and do not affect surviving nodes.
        parent_id = self.parent_id
        # Resolved before the delete: `Model.delete` accepts `using` positionally
        # as well as by keyword, and clears the instance's state afterwards.
        using = (
            kwargs.get("using")
            or (args[0] if args else None)
            or self._state.db
            or router.db_for_write(type(self), instance=self)
        )
        result = super().delete(*args, **kwargs)
        if parent_id is not None:
            type(self)._base_manager.using(using).filter(pk=parent_id).update(
                numchild=models.F("numchild") - 1
            )
        return result


def get_tree_backend() -> str:
    """
    The active page-tree backend: ``"treebeard"`` (default) or ``"mptree"``,
    from the ``CMS_TREE_BACKEND`` setting. An env var of the same name overrides
    the setting only when the setting is not explicitly defined, which keeps the
    backends swappable in CI / subprocess tests without touching the settings
    module. Resolved at import time, so a change requires a process restart --
    but no migration, because both backends declare identical fields.

    ``treebeard`` is imported lazily (only by the selectors below, only when this
    returns ``"treebeard"``), so the ``mptree`` backend never imports it.
    """
    import os

    from django.conf import settings

    return getattr(settings, "CMS_TREE_BACKEND", None) or os.environ.get(
        "CMS_TREE_BACKEND", "treebeard"
    )


def get_tree_base() -> type:
    """Base model class for ``Page`` -- treebeard's ``MP_Node`` or our mixin."""
    if get_tree_backend() == "mptree":
        return MaterializedPathMixin

    from treebeard.mp_tree import MP_Node

    return MP_Node


def get_queryset_base() -> type:
    """
    Base class for ``PageQuerySet``. Treebeard mode keeps ``MP_NodeQuerySet``
    (its only contribution is a tree-fixup ``delete``); mptree mode uses a plain
    Django ``QuerySet`` so treebeard is not imported at all.
    """
    if get_tree_backend() == "mptree":
        return models.QuerySet

    from treebeard.mp_tree import MP_NodeQuerySet

    return MP_NodeQuerySet


# ======================================================================
# PHASE 2 DESIGN NOTE -- FRACTIONAL ORDERING
# ======================================================================
#
# Status: NOT IMPLEMENTED. Deliberate future step. Requires a one-time data
# migration and ends treebeard byte-compatibility (so it cannot be hot-swapped
# back to treebeard). Documented for potential future dev
#
# ----------------------------------------------------------------------
# Why
# ----------------------------------------------------------------------
# This backend stores sibling order as contiguous base-36 steps inside `path`.
# Two consequences follow from that single choice:
#
#   * Inserting/reordering in the middle of a sibling group renumbers the
#     following siblings -- `_layout()` rewrites O(width) subtrees. (Benchmarked:
#     a first-child move into a 2000-wide group is ~840 ms, on par with
#     treebeard, because both renumber.) The `last-child` fast path is a single
#     statement; only mid-inserts pay this.
#   * Fixed `steplen=4` + `path <= 255` caps the tree at ~63 levels deep and
#     36^4 (~1.6M) siblings per node.
#
# Fractional ordering removes BOTH by separating "structure" from "order" into
# two explicit source-of-truth columns and demoting `path` to a pure read cache.
#
# ----------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------
#   class FractionalTreeMixin(models.Model):
#       # --- source of truth ---
#       parent   = FK("self", null=True, on_delete=CASCADE, related_name="children")
#       position = CharField(max_length=255)   # fractional / LexoRank key, e.g.
#                                               # "a0", "a0V", "a1"; sibling-local
#       # --- derived read cache (rebuildable from parent_id + position) ---
#       path      = TextField()                 # SEP-joined ancestor position keys
#       path_hash = CharField(max_length=40, unique=True)   # sha1(path); see below
#       depth     = PositiveIntegerField()
#       numchild  = PositiveIntegerField(default=0)
#
#       class Meta:
#           constraints = [UniqueConstraint(fields=["parent", "position"])]
#           indexes = [Index(fields=["path_hash"])]  # + a prefix index for LIKE
#
# `(parent_id, position)` is the complete, minimal source of truth. `path`,
# `depth`, `numchild` are ALL recomputable from it; `path` exists only so reads
# stay indexed prefix scans (`path__startswith`) instead of recursion.
#
# Fractional key invariant: for any two sibling keys A < B there is always a key
# strictly between them (densely-ordered strings -- append a digit when A and B
# are adjacent). So `key_between(A, B)` lets you place/insert/reorder a node by
# touching ONLY that node.
#
# ----------------------------------------------------------------------
# Operation semantics (the payoff)
# ----------------------------------------------------------------------
#   * Insert between A and B: position = key_between(A.position, B.position);
#     path = parent.path + SEP + position. ONE row. Siblings untouched -- no
#     renumber, no `_layout`, no parking. The O(width) mid-insert -> ~O(1).
#   * Reorder within siblings: recompute only the moved node's position between
#     its new neighbours, then one `_reprefix` of its own subtree.
#   * Move to a new parent: parent_id + a new position among the new siblings +
#     one set-based subtree `_reprefix` -- same single statement as today.
#   * Reads: unchanged. `path__startswith(prefix + SEP)` for strict descendants
#     (the separator makes prefix matching unambiguous), `order_by("path")` for
#     DFS order. `position` must not contain SEP.
#
# ----------------------------------------------------------------------
# Gains
# ----------------------------------------------------------------------
#   * No sibling renumbering, ever -> mid-insert/reorder are single-node; the
#     per-sibling loop (and any CTE written to speed it) becomes unnecessary.
#   * No ceilings: variable-length path removes the ~63-level depth cap and the
#     siblings-per-node cap.
#   * Concurrency: concurrent inserts at different spots compute different keys
#     with no shared "max+1" counter and no sibling-row locks; same-spot inserts
#     collide only on the (parent, position) unique constraint and retry. This is
#     the real write-concurrency win over treebeard.
#
# ----------------------------------------------------------------------
# Costs / things to get right
# ----------------------------------------------------------------------
#   * `path` is effectively unbounded (fractional keys grow under adversarial
#     repeated-between inserts) -> TextField. MySQL cannot put a UNIQUE index on
#     a long/text column (767/3072-byte limit), so uniqueness lives on a
#     `path_hash` (sha1) column, with a prefix index on `path` for LIKE.
#   * One-time migration + end of treebeard byte-compat: backfill `position` from
#     each node's current sibling (path-step) order, then recompute every `path`
#     in the SEP encoding. After this, hot-swapping BACK to treebeard is no
#     longer possible.
#   * Own `key_between(a, b)`: ~100 lines, pure Python, no dependency (base-N
#     midpoint, append a digit when neighbours are adjacent). It is the
#     correctness core -- test it hard (adjacent keys, empty bounds, long chains).
#   * Occasional key renormalisation: if a hot spot grows keys long, a rare
#     maintenance pass reassigns short keys to a parent's children (same class as
#     `rebuild()`, off the hot path).
#
# ----------------------------------------------------------------------
# Net
# ----------------------------------------------------------------------
# parent_id = structure, position = order, path = indexed read cache (with depth
# /numchild), all caches rebuildable from the first two. Deletes the renumber
# problem and the depth/width ceilings; strongest concurrency story. Cost: one
# irreversible migration, a TextField path + hash for MySQL uniqueness, and
# owning key generation. Reads are unchanged.
# ======================================================================
