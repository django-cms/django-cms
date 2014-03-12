# -*- coding: utf-8 -*-
from django.db.models import Q
from django.contrib.sites.models import Site
from cms.publisher.query import PublisherQuerySet
from cms.exceptions import NoHomeFound
from django.utils import timezone


class PageQuerySet(PublisherQuerySet):
    def on_site(self, site=None):
        if not site:
            try:
                site = Site.objects.get_current()
            except Site.DoesNotExist:
                site = None
        return self.filter(site=site)

    def root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For
        current site - used in frontend
        """
        return self.on_site().filter(parent__isnull=True)

    def all_root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For
        all sites - used in frontend
        """
        return self.filter(parent__isnull=True)

    def valid_targets(self, page_id, request, perms, page=None):
        """
        Give valid targets to move a page into the tree
        """
        if page is None:
            page = self.get(pk=page_id)
        exclude_list = []
        if page:
            exclude_list.append(page.id)
            for p in page.get_descendants():
                exclude_list.append(p.id)
        if perms != "All":
            return self.filter(id__in=perms).exclude(id__in=exclude_list)
        else:
            return self.exclude(id__in=exclude_list)

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

    def expired(self):
        return self.on_site().filter(
            publication_end_date__lte=timezone.now())

    def get_all_pages_with_application(self):
        """Returns all pages containing applications for all sites.

        Doesn't cares about the application language.
        """
        return self.published().filter(title_set__application_urls__gt='').distinct()

    def get_home(self, site=None):
        try:
            home = self.published(site=site).all_root().order_by("tree_id")[0]
        except IndexError:
            raise NoHomeFound('No Root page found. Publish at least one page!')
        return home
