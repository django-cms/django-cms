# -*- coding: utf-8 -*-
from django.db import models
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
        return self.filter(site=site)

    def published(self, language=None):
        if language:
            pub = self.filter(
                Q(publication_date__lte=timezone.now()) | Q(publication_date__isnull=True),
                Q(publication_end_date__gt=timezone.now()) | Q(publication_end_date__isnull=True),
                title_set__published=True, title_set__language=language
            )
        else:
            pub = self.filter(
                Q(publication_date__lte=timezone.now()) | Q(publication_date__isnull=True),
                Q(publication_end_date__gt=timezone.now()) | Q(publication_end_date__isnull=True),
                title_set__published=True
            )
        return pub

    def get_home(self, site=None):
        try:
            home = self.published().distinct().on_site(site).get(is_home=True)
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
        """
        Optimized delete method for page nodes.
        Updates parent numchild to reflect new count.
        """
        parents = self.exclude(parent__isnull=True).values_list('parent')
        (self
         .model
         .objects
         .filter(pk__in=parents)
         .update(numchild=models.F('numchild') - 1))
        super(MP_NodeQuerySet, self).delete()

    def root_only(self):
        return self.filter(depth=1)
