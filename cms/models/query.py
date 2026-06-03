import warnings
from collections import Counter

from django.db import models
from django.db.models import F
from django.db.models.functions import Greatest

from cms.exceptions import NoHomeFound
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from cms.utils.mptree import get_queryset_base, get_tree_backend

# Resolved once at import time (same as the model base in pagemodel.py). In
# mptree mode the base is a plain QuerySet and treebeard is never imported.
_USING_TREEBEARD = get_tree_backend() == "treebeard"


class PageQuerySet(get_queryset_base()):

    node_warning = ("As of django CMS 5.0 the Page model does not have a node property anymore. "
                    "Use the related fields directly.")

    def delete(self, *args, **kwargs):
        if _USING_TREEBEARD:
            # treebeard's MP_NodeQuerySet.delete removes whole subtrees by path
            # and fixes parent numchild.
            return super().delete(*args, **kwargs)
        # mptree backend: the parent FK's on_delete=CASCADE removes descendants
        # (no orphans), but the surviving parents' numchild cache still needs
        # decrementing -- mirror treebeard's behaviour using parent_id instead
        # of path. (Instance .delete() is handled on the model mixin; this path
        # covers bulk ``Page.objects.filter(...).delete()``.)
        rows = list(self.values_list("pk", "parent_id"))
        deleted = {pk for pk, _ in rows}
        lost = Counter(
            parent_id for _, parent_id in rows
            if parent_id is not None and parent_id not in deleted
        )
        result = models.QuerySet.delete(self, *args, **kwargs)
        for parent_id, num_lost in lost.items():
            self.model._base_manager.filter(pk=parent_id).update(
                numchild=Greatest(F("numchild") - num_lost, 0)
            )
        return result

    def get_descendants(self, parent=None):
        if parent is None:
            return self.all()

        if parent.is_leaf():
            # leaf nodes have no children
            return self.none()
        return self.filter(path__startswith=parent.path, depth__gte=parent.depth)

    def on_site(self, site=None):
        from django.contrib.sites.models import Site

        if site is None:
            site = Site.objects.get_current()
        return self.filter(site=site)

    def get_home(self, site=None):
        try:
            home = self.on_site(site).distinct().get(is_home=True)
        except self.model.DoesNotExist:
            raise NoHomeFound('No Root page found')
        return home

    def has_apphooks(self):
        """
        Returns True if any page on this queryset has an apphook attached.
        """
        return self.exclude(application_urls=None).exclude(application_urls='').exists()

    def delete_fast(self):
        # plain Django delete, skipping any tree-fixup delete (both backends)
        models.QuerySet.delete(self)

    def root_only(self):
        return self.filter(depth=1)

    def select_related(self, *fieldnames):
        modified = []
        for f in fieldnames:
            if isinstance(f, str) and f.startswith('node'):
                warnings.warn(
                    self.node_warning,
                    RemovedInDjangoCMS60Warning,
                    stacklevel=2,
                )
                if f != 'node':
                    modified.append(f.replace('node__', ''))
            else:
                modified.append(f)
        return super().select_related(*modified)

    def filter(self, *args, **kwargs):
        modified = {}
        for key, val in kwargs.items():
            if isinstance(key, str) and key.startswith('node'):
                warnings.warn(
                    self.node_warning,
                    RemovedInDjangoCMS60Warning,
                    stacklevel=2,
                )
                if key == 'node':
                    continue
                modified[key[6:]] = val
            else:
                modified[key] = val
        return super().filter(*args, **modified)

    def order_by(self, *fieldnames):
        modified = []
        for f in fieldnames:
            if isinstance(f, str) and f.startswith("node__"):
                warnings.warn(
                    self.node_warning,
                    RemovedInDjangoCMS60Warning,
                    stacklevel=2,
                )
                modified.append(f[6:])
            else:
                modified.append(f)
        return super().order_by(*modified)
