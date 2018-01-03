# -*- coding: utf-8 -*-
from django.db.models import Q
from django.utils import timezone

from treebeard.mp_tree import MP_NodeQuerySet

from cms.publisher.query import PublisherQuerySet
from cms.exceptions import NoHomeFound


class PageQuerySet(PublisherQuerySet):

    def on_site(self, site=None):
        from cms.utils import get_current_site

        if site is None:
            site = get_current_site()
        return self.filter(node__site=site)

    def published(self, site=None, language=None):
        now = timezone.now()
        if language:
            pub = self.on_site(site).filter(
                Q(publication_date__lte=now) | Q(publication_date__isnull=True),
                Q(publication_end_date__gt=now) | Q(publication_end_date__isnull=True),
                title_set__published=True, title_set__language=language,
            )
        else:
            pub = self.on_site(site).filter(
                Q(publication_date__lte=now) | Q(publication_date__isnull=True),
                Q(publication_end_date__gt=now) | Q(publication_end_date__isnull=True),
                title_set__published=True,
            )
        return pub.exclude(title_set__publisher_state=4)

    def get_home(self, site=None):
        try:
            home = self.published(site).distinct().get(is_home=True)
        except self.model.DoesNotExist:
            raise NoHomeFound('No Root page found. Publish at least one page!')
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
