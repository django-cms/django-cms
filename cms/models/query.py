import warnings

from treebeard.mp_tree import MP_NodeQuerySet

from cms.exceptions import NoHomeFound
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning


class PageQuerySet(MP_NodeQuerySet):

    node_warning = ("As of django CMS 5.0 the Page model does not have a node property anymore. "
                    "Use the related fields directly.")

    def get_descendants(self, parent=None):
        if parent is None:
            return self.all()

        if parent.is_leaf():
            # leaf nodes have no children
            return self.none()
        return self.filter(path__startswith=parent.path, depth__gte=parent.depth)

    def on_site(self, site=None):
        from cms.utils import get_current_site

        if site is None:
            site = get_current_site()
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
        # calls django's delete instead of the one from treebeard
        super(MP_NodeQuerySet, self).delete()

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
        return super().order_by(*fieldnames)
