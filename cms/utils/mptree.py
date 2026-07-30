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
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import wraps

from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models, router, transaction
from django.db.models import F, Value
from django.db.models.functions import Concat, Length, Substr

DEFAULT_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_STEPLEN = 4
CHILD_POSITIONS = frozenset({"first-child", "last-child"})
SIBLING_POSITIONS = frozenset({"first-sibling", "last-sibling", "left", "right"})
MOVE_POSITIONS = CHILD_POSITIONS | frozenset({"left", "right"})
_MISSING = object()


class InvalidTreePosition(ValueError):
    """Raised when a tree mutation receives an unsupported position."""


class InvalidTreeConfiguration(ValueError):
    """Raised when materialized-path encoding options are unsafe."""


class TreePathOverflow(ValueError):
    """Raised when a tree position cannot fit its path representation."""


class TreeCorruptionError(ValueError):
    """Raised when parent relationships cannot form a complete forest."""

    def __init__(self, message, *, node_ids):
        super().__init__(message)
        self.node_ids = set(node_ids)


class TreeScopeError(ValueError):
    """Raised when a mutation would cross a tree namespace such as a site."""


@dataclass(frozen=True)
class TreeIssue:
    code: str
    node_id: object
    message: str


def _validate_position(position, supported):
    if position not in supported:
        choices = ", ".join(sorted(supported))
        raise InvalidTreePosition(
            f"Unsupported tree position {position!r}; expected one of: {choices}."
        )


def _atomic_on_driver(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with transaction.atomic(using=self.db_alias):
            return method(self, *args, **kwargs)

    return wrapped


def lock_tree_namespace(model, using):
    """Lock the stable row that serializes a model's global page-path space."""
    try:
        site_field = model._meta.get_field("site")
    except FieldDoesNotExist:
        return False
    site_model = site_field.remote_field.model
    return (
        site_model._base_manager.using(using)
        .order_by("pk")
        .select_for_update()
        .values_list("pk", flat=True)
        .first()
        is not None
    )


class TreeBackend(str, Enum):
    """Supported page-tree implementations."""

    TREEBEARD = "treebeard"
    MPTREE = "mptree"

    @property
    def uses_treebeard(self):
        return self is self.TREEBEARD

    def ensure_valid(self):
        return None

    @property
    def model_base(self):
        if self is self.MPTREE:
            return MaterializedPathMixin

        from treebeard.mp_tree import MP_Node

        return MP_Node

    @property
    def queryset_base(self):
        if self is self.MPTREE:
            return models.QuerySet

        from treebeard.mp_tree import MP_NodeQuerySet

        return MP_NodeQuerySet


@dataclass(frozen=True)
class InvalidTreeBackend:
    """Safe model-loading descriptor for an invalid configured backend."""

    configured: object
    uses_treebeard = False
    queryset_base = models.QuerySet

    @property
    def model_base(self):
        return MaterializedPathMixin

    def ensure_valid(self):
        raise ImproperlyConfigured(
            f"CMS_TREE_BACKEND has unsupported value {self.configured!r}; "
            "use 'treebeard' or 'mptree'."
        )


def _configured_tree_backend():
    """Return the explicit setting, or the environment/default fallback."""
    import os

    configured = getattr(settings, "CMS_TREE_BACKEND", _MISSING)
    if configured is _MISSING:
        return os.environ.get("CMS_TREE_BACKEND", TreeBackend.TREEBEARD.value)
    return configured


def _resolve_tree_backend(configured):
    try:
        return TreeBackend(configured)
    except (TypeError, ValueError):
        return None


@register()
def check_tree_backend(app_configs=None, **kwargs):
    """Report invalid backend names without allowing selector disagreement."""
    configured = _configured_tree_backend()
    if _resolve_tree_backend(configured) is not None:
        return []
    return [
        Error(
            f"CMS_TREE_BACKEND has unsupported value {configured!r}.",
            hint="Use 'treebeard' or 'mptree'.",
            id="cms.E002",
        )
    ]


class MaterializedPath:
    """
    Set-based materialized-path operations for a model with the treebeard
    column layout: ``path`` (unique CharField), ``depth``, ``numchild`` and a
    self-referential ``parent`` FK.

    ``scope`` is an optional dict of field lookups that partitions the forest
    (e.g. ``{"site_id": 3}``). It defaults to no scope, i.e. the whole table is
    one forest -- matching treebeard's behaviour for the page tree.
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
        if not isinstance(steplen, int) or isinstance(steplen, bool) or steplen < 1:
            raise InvalidTreeConfiguration("steplen must be a positive integer.")
        if not isinstance(alphabet, str) or len(alphabet) < 2:
            raise InvalidTreeConfiguration("alphabet must contain at least two symbols.")
        if len(set(alphabet)) != len(alphabet):
            raise InvalidTreeConfiguration("alphabet symbols must be unique.")
        self.model = model
        self.steplen = steplen
        self.alphabet = alphabet
        self.radix = len(alphabet)
        self.path_max_length = model._meta.get_field("path").max_length
        self.has_site_namespace = any(
            field.name == "site"
            for field in model._meta.get_fields()
        )
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
        if step < 1 or step >= self.radix ** self.steplen:
            raise TreePathOverflow(
                f"Sibling step {step} does not fit in a {self.steplen}-character "
                f"base-{self.radix} path segment."
            )
        key = self._int2str(step)
        return self.alphabet[0] * (self.steplen - len(key)) + key

    def _ensure_path_fits(self, path):
        self._ensure_path_length_fits(len(path))

    def _ensure_path_length_fits(self, required):
        if self.path_max_length is not None and required > self.path_max_length:
            raise TreePathOverflow(
                f"Path requires {required} characters but "
                f"{self.model._meta.label}.path allows {self.path_max_length}."
            )

    def _validate_namespace(self, reference, instance, attrs):
        if not self.has_site_namespace:
            return
        if instance is not None:
            site_id = instance.site_id
        elif "site_id" in attrs:
            site_id = attrs["site_id"]
        elif "site" in attrs:
            site = attrs["site"]
            site_id = site.pk if hasattr(site, "pk") else site
        else:
            site_id = None
        if site_id is not None and site_id != reference.site_id:
            raise TreeScopeError(
                f"Cannot place a {self.model._meta.label} from site {site_id} "
                f"in the tree for site {reference.site_id}."
            )

    def step_of(self, path):
        """Decode the last (own) segment of ``path`` back to its integer step."""
        return self._str2int(path[-self.steplen :])

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

    def validate(self):
        """Return tree invariant violations without modifying any rows."""
        field_names = {field.name for field in self.model._meta.get_fields()}
        values = ["pk", "parent_id", "path", "depth", "numchild"]
        if "site" in field_names:
            values.append("site_id")
        rows = list(self._scoped().order_by("path").values(*values))
        by_pk = {row["pk"]: row for row in rows}
        present = set(by_pk)
        children = defaultdict(list)
        issues = []
        invalid_paths = set()

        for row in rows:
            node_id = row["pk"]
            parent_id = row["parent_id"]
            path = row["path"]
            children[parent_id].append(node_id)

            if parent_id is not None and parent_id not in present:
                issues.append(
                    TreeIssue(
                        "parent",
                        node_id,
                        f"parent {parent_id} is outside the tree scope",
                    )
                )
            elif (
                "site_id" in row
                and parent_id is not None
                and row["site_id"] != by_pk[parent_id]["site_id"]
            ):
                issues.append(
                    TreeIssue(
                        "site",
                        node_id,
                        f"site {row['site_id']} differs from parent site "
                        f"{by_pk[parent_id]['site_id']}",
                    )
                )

            path_is_valid = (
                bool(path)
                and len(path) % self.steplen == 0
                and (
                    self.path_max_length is None
                    or len(path) <= self.path_max_length
                )
                and all(char in self.alphabet for char in path)
            )
            if path_is_valid:
                path_is_valid = all(
                    self._str2int(path[index : index + self.steplen]) > 0
                    for index in range(0, len(path), self.steplen)
                )
            if not path_is_valid:
                invalid_paths.add(node_id)
                issues.append(
                    TreeIssue("path", node_id, f"invalid encoded path {path!r}")
                )

        structural_depth = {}
        stack = [
            (node_id, 1)
            for node_id in reversed(children.get(None, []))
        ]
        while stack:
            node_id, depth = stack.pop()
            if node_id in structural_depth:
                continue
            structural_depth[node_id] = depth
            stack.extend(
                (child_id, depth + 1)
                for child_id in reversed(children.get(node_id, []))
            )

        for node_id in present - structural_depth.keys():
            issues.append(
                TreeIssue(
                    "parent",
                    node_id,
                    "node is unreachable from any root, likely due to a parent cycle",
                )
            )

        for node_id, row in by_pk.items():
            depth = structural_depth.get(node_id)
            numchild = len(children.get(node_id, []))
            parent = by_pk.get(row["parent_id"])
            path_has_structure = (
                len(row["path"]) == self.steplen
                if parent is None
                else (
                    row["path"].startswith(parent["path"])
                    and len(row["path"]) == len(parent["path"]) + self.steplen
                )
            )
            if not path_has_structure and node_id not in invalid_paths:
                issues.append(
                    TreeIssue(
                        "path",
                        node_id,
                        f"stored {row['path']!r} does not identify one step "
                        "below its parent",
                    )
                )
            if depth is not None and row["depth"] != depth:
                issues.append(
                    TreeIssue(
                        "depth",
                        node_id,
                        f"stored {row['depth']}, expected {depth}",
                    )
                )
            if row["numchild"] != numchild:
                issues.append(
                    TreeIssue(
                        "numchild",
                        node_id,
                        f"stored {row['numchild']}, expected {numchild}",
                    )
                )

        return sorted(issues, key=lambda issue: (str(issue.node_id), issue.code))

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
                self.model._base_manager.using(self.db_alias).filter(pk__in=pks)
                .order_by("pk")
                .select_for_update()
            )

    def _lock_namespace(self):
        if self.lock:
            return lock_tree_namespace(self.model, self.db_alias)
        return False

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
        # `parent`/`parent_id` are determined by the tree operation, not by the
        # caller's kwargs (treebeard's add_child/add_sibling accept them as
        # redundant field values) -- drop them so they can't conflict.
        self._ensure_path_fits(path)
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

    @_atomic_on_driver
    def add_root(self, instance=None, **attrs):
        if not self._lock_namespace():
            self._lock_rows(*self.roots().values_list("pk", flat=True))
        step = self._last_root_step() + 1
        return self._materialise(
            instance, attrs, path=self.segment(step), depth=1, parent=None
        )

    @_atomic_on_driver
    def add_child(self, parent, position="last-child", instance=None, **attrs):
        _validate_position(position, CHILD_POSITIONS)
        self._validate_namespace(parent, instance, attrs)
        self._lock_namespace()
        self._lock_rows(parent.pk)
        parent.refresh_from_db(using=self.db_alias)
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
            node.refresh_from_db(using=self.db_alias)
        return node

    @_atomic_on_driver
    def add_sibling(self, node, position="last-sibling", instance=None, **attrs):
        _validate_position(position, SIBLING_POSITIONS)
        self._validate_namespace(node, instance, attrs)
        self._lock_namespace()
        self._lock_rows(node.pk)
        node.refresh_from_db(using=self.db_alias)
        parent = node.parent
        if parent is None:
            new = self.add_root(instance=instance, **attrs)
            if position != "last-sibling":
                self._place_relative(new, node, position=position)
            return new
        new = self.add_child(parent, instance=instance, **attrs)
        if position != "last-sibling":
            self._place_relative(new, node, position=position)
        return new

    def _place_relative(self, node, sibling, *, position):
        parent = sibling.parent
        parent_path = parent.path if parent else ""
        parent_depth = parent.depth if parent else 0
        order = [pk for pk in self._ordered_child_pks(parent_path, parent_depth) if pk != node.pk]
        if position == "first-sibling":
            idx = 0
        else:
            idx = order.index(sibling.pk) + (1 if position == "right" else 0)
        order.insert(idx, node.pk)
        self._layout(parent_path, parent_depth, order)
        node.refresh_from_db(using=self.db_alias)

    # -- move (single statement for append; layout for insert) -----------

    @_atomic_on_driver
    def move(self, node, target, pos="last-child"):
        """
        Move ``node`` (and its whole subtree). Supported ``pos``:
        ``last-child``/``first-child`` (relative to ``target``) and
        ``left``/``right`` (relative to sibling ``target``).
        """
        _validate_position(pos, MOVE_POSITIONS)
        self._lock_namespace()
        self._lock_rows(node.pk, target.pk)
        node.refresh_from_db(using=self.db_alias)
        target.refresh_from_db(using=self.db_alias)
        if self.has_site_namespace and node.site_id != target.site_id:
            raise TreeScopeError(
                f"Cannot move a {self.model._meta.label} from site "
                f"{node.site_id} to site {target.site_id}."
            )
        old_parent_id = node.parent_id
        if pos in ("left", "right"):
            new_parent_id = target.parent_id
            self._lock_rows(old_parent_id, new_parent_id)
            new_parent = (
                self.model._base_manager.using(self.db_alias).get(pk=new_parent_id)
                if new_parent_id is not None
                else None
            )
        else:
            new_parent = target
            self._lock_rows(old_parent_id)

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
        node.refresh_from_db(using=self.db_alias)
        target.refresh_from_db(using=self.db_alias)

    # -- rebuild (recompute everything from parent_id) -------------------

    @_atomic_on_driver
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
        self._lock_namespace()
        rows = list(
            self._scoped().order_by("path").values("pk", "parent_id")
        )
        present = {r["pk"] for r in rows}
        outside_scope = {
            r["pk"]
            for r in rows
            if r["parent_id"] is not None and r["parent_id"] not in present
        }
        if outside_scope:
            raise TreeCorruptionError(
                "Cannot rebuild nodes whose parents are outside the tree scope.",
                node_ids=outside_scope,
            )
        children = defaultdict(list)
        for r in rows:
            # rows are in path order, so each parent's children list is built in
            # sibling order
            children[r["parent_id"]].append(r["pk"])

        computed = {}
        stack = [(None, "", 1)]
        while stack:
            parent_pk, parent_path, depth = stack.pop()
            for step, pk in enumerate(children.get(parent_pk, []), start=1):
                path = parent_path + self.segment(step)
                self._ensure_path_fits(path)
                computed[pk] = [path, depth, len(children.get(pk, []))]
                stack.append((pk, path, depth + 1))

        unreachable = present - computed.keys()
        if unreachable:
            raise TreeCorruptionError(
                "Cannot rebuild a tree containing parent cycles or unreachable nodes.",
                node_ids=unreachable,
            )

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
        get_tree_backend().ensure_valid()
        return MaterializedPath(
            cls,
            steplen=cls.steplen,
            alphabet=cls.alphabet,
            using=using,
        )

    def _instance_tree(self):
        return type(self)._tree(using=self._state.db)

    # -- treebeard-compatible API ---------------------------------------

    @classmethod
    def add_root(cls, instance=None, **attrs):
        using = None
        if instance is not None:
            using = instance._state.db or router.db_for_write(
                cls,
                instance=instance,
            )
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

    @classmethod
    def validate_tree(cls, using=None):
        return cls._tree(using=using).validate()

    def add_child(self, instance=None, **attrs):
        attrs.pop("parent", None)  # redundant: the parent is `self`
        return self._instance_tree().add_child(self, instance=instance, **attrs)

    def add_sibling(self, pos="last-sibling", instance=None, **attrs):
        attrs.pop("parent", None)
        attrs.pop("parent_id", None)
        return self._instance_tree().add_sibling(
            self,
            position=pos,
            instance=instance,
            **attrs,
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
        result = super().delete(*args, **kwargs)
        if parent_id is not None:
            type(self)._base_manager.filter(pk=parent_id).update(
                numchild=models.F("numchild") - 1
            )
        return result


_CONFIGURED_TREE_BACKEND = _configured_tree_backend()
_ACTIVE_TREE_BACKEND = _resolve_tree_backend(_CONFIGURED_TREE_BACKEND)
if _ACTIVE_TREE_BACKEND is None:
    _ACTIVE_TREE_BACKEND = InvalidTreeBackend(_CONFIGURED_TREE_BACKEND)


def get_tree_backend():
    """Return the process-wide, centrally resolved page-tree backend."""
    return _ACTIVE_TREE_BACKEND


def get_tree_base():
    """Base model class for ``Page`` -- treebeard's ``MP_Node`` or our mixin."""
    return get_tree_backend().model_base


def get_queryset_base():
    """Return the queryset base supplied by the active backend."""
    return get_tree_backend().queryset_base
