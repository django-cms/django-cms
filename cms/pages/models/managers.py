# ruff: noqa: W605
"""Managers for the page models.

``WithUserMixin`` lives here rather than in a shared module because only the page
content managers use it: it threads the acting user through a queryset so that
permission-aware managers can filter on it.
"""
from django.db import models
from django.db.models import Q

from cms.pages.models.query import PageQuerySet


class PageManager(models.Manager):

    def get_queryset(self):
        """Change standard model queryset to our own.
        """
        return PageQuerySet(self.model)

    # Just some of the queryset methods are implemented here, access queryset
    # for more getting more supporting methods.

    def on_site(self, site=None):
        return self.get_queryset().on_site(site)

    def get_home(self, site=None):
        return self.get_queryset().get_home(site)

    def search(self, q, language=None, current_site_only=True, site=None):
        """Pages whose public content matches ``q``.

        A page matches if the title of its public content, or a ``search_fields``
        field of one of the plugins in it, contains ``q``, case-insensitively; in
        ``language`` if given. Only public content is searched
        (``PageContent.objects``; with djangocms-versioning, the published
        version), so a page never matches by text only a draft contains.
        """
        from cms.pages.models.content import PageContent

        qs = self.get_queryset()

        if site or current_site_only:
            qs = qs.on_site(site)

        matching = search_page_contents(PageContent.objects.all(), q, language)
        return qs.filter(pk__in=matching.values("page_id")).distinct()


def search_page_contents(page_contents, q, language=None):
    """The contents among ``page_contents`` matching ``q``, as :meth:`PageManager.search` matches.

    Their title, or a ``search_fields`` field of one of their plugins, contains
    ``q``, case-insensitively; with ``language``, plugins in that language and
    contents in it. ``page_contents`` decides which content is searched: the
    public content, or the editor's (``PageContent.admin_manager``).
    """
    from cms.core.plugin_pool import plugin_pool

    qt = Q(title__icontains=q)

    # find 'searchable' plugins and build query
    qp = Q()
    for plugin in plugin_pool.registered_plugins:
        cmsplugin = plugin.model
        if not (
            hasattr(cmsplugin, 'search_fields') and hasattr(cmsplugin, 'cmsplugin_ptr')
        ):
            continue
        field = cmsplugin.cmsplugin_ptr.field
        related_query_name = field.related_query_name()
        if related_query_name and not related_query_name.startswith('+'):
            for field in cmsplugin.search_fields:
                qp |= Q(**{f'placeholders__cmsplugin__{related_query_name}__{field}__icontains': q})
    if language:
        qt &= Q(language=language)
        qp &= Q(placeholders__cmsplugin__language=language)

    return page_contents.filter(qt | qp).distinct()


class WithUserMixin:
    """empty mixin adds with_user """
    def with_user(self, user):
        return self


class PageUrlManager(WithUserMixin, models.Manager):
    def get_for_site(self, site, **kwargs):
        kwargs['site'] = site
        return self.filter(**kwargs)


class PageContentManager(WithUserMixin, models.Manager):
    pass


class ContentAdminQuerySet(models.QuerySet):
    def current_content(self, **kwargs):
        """If a versioning package is installed, this returns the currently valid content
        that matches the filter given in kwargs. Used to find content to be copied, e.g..
        Without versioning every page is current."""
        return self.filter(**kwargs)

    def latest_content(self, **kwargs):
        """If a versioning package is installed, returns the latest version that matches the
        filter given in kwargs including discarded or unpublished page content. Without versioning
        every page content is the latest."""
        return self.filter(**kwargs)


class ContentAdminManager(WithUserMixin, models.Manager):
    def get_queryset(self):
        return ContentAdminQuerySet(self.model, using=self._db)

    def current_content(self, **kwargs):
        """Syntactic sugar: admin_manager.current_content()"""
        return self.get_queryset().current_content(**kwargs)

    def latest_content(self, **kwargs):
        """Syntactic sugar: admin_manager.latest_content()"""
        return self.get_queryset().latest_content(**kwargs)
