# ruff: noqa: W605
"""Managers for the page models.

``WithUserMixin`` lives here rather than in a shared module because only the page
content managers use it: it threads the acting user through a queryset so that
permission-aware managers can filter on it.
"""
from django.db import models
from django.db.models import Q

from cms.pages.models.query import PageQuerySet
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from cms.utils.i18n import get_fallback_languages


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
        """Simple search function

        Plugins can define a 'search_fields' tuple similar to ModelAdmin classes
        """
        from cms.core.plugin_pool import plugin_pool

        qs = self.get_queryset()

        if site or current_site_only:
            qs = qs.on_site(site)

        qt = Q(pagecontent_set__title__icontains=q)

        # find 'searchable' plugins and build query
        qp = Q()
        plugins = plugin_pool.registered_plugins
        for plugin in plugins:
            cmsplugin = plugin.model
            if not (
                hasattr(cmsplugin, 'search_fields') and hasattr(cmsplugin, 'cmsplugin_ptr')
            ):
                continue
            field = cmsplugin.cmsplugin_ptr.field
            related_query_name = field.related_query_name()
            if related_query_name and not related_query_name.startswith('+'):
                for field in cmsplugin.search_fields:
                    qp |= Q(**{
                        f'pagecontent_set__placeholders__cmsplugin__{related_query_name}__{field}__icontains': q})
        if language:
            qt &= Q(pagecontent_set__language=language)
            qp &= Q(pagecontent_set__placeholders__cmsplugin__language=language)

        qs = qs.filter(qt | qp)

        return qs.distinct()


class WithUserMixin:
    """empty mixin adds with_user """
    def with_user(self, user):
        return self


class PageUrlManager(WithUserMixin, models.Manager):
    def get_for_site(self, site, **kwargs):
        kwargs['site'] = site
        return self.filter(**kwargs)


class PageContentManager(WithUserMixin, models.Manager):
    def get_title(self, page, language, language_fallback=False):
        """
        Gets the latest content for a particular page and language. Falls back
        to another language if wanted.
        """
        import warnings

        warnings.warn(
            "PageContentManager.get_title is deprecated and will be removed in a future release. "
            "Please use page.get_page_content() or page.get_admin_content() instead.",
            RemovedInDjangoCMS60Warning,
            stacklevel=2,
        )
        try:
            title = self.get(language=language, page=page)
            return title
        except self.model.DoesNotExist:
            if language_fallback:
                try:
                    titles = self.filter(page=page)
                    fallbacks = get_fallback_languages(language, site_id=page.site_id)
                    for lang in fallbacks:
                        for title in titles:
                            if lang == title.language:
                                return title
                    return None
                except self.model.DoesNotExist:
                    pass
            else:
                raise
        return None


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
