from django.db.models.query import QuerySet
from treebeard.mp_tree import MP_NodeQuerySet

from cms.exceptions import NoHomeFound


class PageQuerySet(QuerySet):

    def on_site(self, site=None):
        from cms.utils import get_current_site

        if site is None:
            site = get_current_site()
        return self.filter(node__site=site)

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


class PageNodeQuerySet(MP_NodeQuerySet):

    def get_descendants(self, parent=None):
        if parent is None:
            return self.all()

        if parent.is_leaf():
            # leaf nodes have no children
            return self.none()
        return self.filter(path__startswith=parent.path, depth__gte=parent.depth)

    def delete_fast(self):
        # calls django's delete instead of the one from treebeard
        super(MP_NodeQuerySet, self).delete()

    def root_only(self):
        return self.filter(depth=1)
