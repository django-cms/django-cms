# -*- coding: utf-8 -*-
from django.db.models import Q
from django.contrib.sites.models import Site
from treebeard.mp_tree import MP_NodeQuerySet
from cms.publisher.query import PublisherQuerySet
from cms.exceptions import NoHomeFound
from django.utils import timezone


class PageQuerySet(MP_NodeQuerySet, PublisherQuerySet):
    def on_site(self, site=None):
        if not site:
            try:
                site = Site.objects.get_current()
            except Site.DoesNotExist:
                site = None
        return self.filter(site=site)

    def all_root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For
        all sites - used in frontend
        """
        return self.filter(parent__isnull=True)

    def published(self, language=None, site=None):

        if language:
            pub = self.on_site(site).filter(
                Q(publication_date__lte=timezone.now()) | Q(publication_date__isnull=True),
                Q(publication_end_date__gt=timezone.now()) | Q(publication_end_date__isnull=True),
                title_set__published=True, title_set__language=language
            )
        else:
            pub = self.on_site(site).filter(
                Q(publication_date__lte=timezone.now()) | Q(publication_date__isnull=True),
                Q(publication_end_date__gt=timezone.now()) | Q(publication_end_date__isnull=True),
                title_set__published=True
            )
        return pub

    def get_home(self, site=None):
        try:
            home = self.published(site=site).all_root().order_by("path")[0]
        except IndexError:
            raise NoHomeFound('No Root page found. Publish at least one page!')
        return home
