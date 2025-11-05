from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.db.models import OuterRef, Q, QuerySet, Subquery

from cms.models import PageContent, PageUrl
from cms.utils.i18n import get_public_languages


def from_iterable(iterables):
    """
    Backport of itertools.chain.from_iterable
    """
    for it in iterables:
        yield from it


class CMSSitemap(Sitemap):
    """
    Sitemap for django CMS pages limited to public, non-redirecting, and anonymously
    accessible content on the current Site.

    Targets the current Site and respects the project's public languages. Pages are
    annotated with the latest ``PageContent.changed_date`` and exposes it via ``lastmod()``.

    Enable the sitemap framework and register the sitemap in your URL configuration.

    .. code-block:: python

       # settings.py
       INSTALLED_APPS = [
           # ...
           "django.contrib.sitemaps",
       ]

    .. code-block:: python

       # urls.py
       from django.contrib.sitemaps import views as sitemap_views
       from cms.sitemaps.cms_sitemap import CMSSitemap

       sitemaps = {
           "pages": CMSSitemap,
       }

       urlpatterns = [
           path("sitemap.xml", sitemap_views.sitemap, {"sitemaps": sitemaps}, name="sitemap"),
       ]
   """

    changefreq: str = "monthly"
    priority: float = 0.5
    site = None

    def items(self) -> QuerySet:
        """
        Items are PageUrl instances for the current Site, filtered to only include
        those that are:

        - In a public language for the Site
        - Not redirects
        - Not login_required

        The site is taken from the ``SITE_ID`` setting or identified from the current request
        using the Sites framework. (A custom site middelware is ignored by Django's sitemap
        framework.)
        """
        #
        # It is counter-productive to provide entries for:
        #   > Pages which redirect:
        #       - If the page redirects to another page on this site, the
        #         destination page will already be in the sitemap, and
        #       - If the page redirects externally, then it shouldn't be
        #         part of our sitemap anyway.
        #   > Pages which cannot be accessed by anonymous users (like
        #     search engines are).
        #
        # It is noted here: http://www.sitemaps.org/protocol.html that
        # "locations" that differ from the place where the sitemap is found,
        # are considered invalid. E.g., if your sitemap is located here:
        #
        #     http://example.com/sub/sitemap.xml
        #
        # valid locations *must* be rooted at http://example.com/sub/...
        #
        # This rules any redirected locations out.
        #
        # If, for some reason, you require redirecting pages (PageContent) to be
        # included, simply create a new class inheriting from this one, and
        # supply a new items() method which doesn't filter out the redirects.
        #
        # Even though items() can also return a sequence, we should return a
        # QuerySet in this case in order to be compatible with
        # djangocms-page-sitemap.
        site = self.site or Site.objects.get_current()
        languages = get_public_languages(site_id=site.pk)
        return (
            PageUrl.objects.get_for_site(site)
            .filter(language__in=languages, path__isnull=False, page__login_required=False)
            .order_by("page__path")
            .select_related("page")
            .annotate(
                content_changed_date=Subquery(
                    PageContent.objects.filter(page=OuterRef("page"), language=OuterRef("language"))
                    .filter(Q(redirect="") | Q(redirect=None))
                    .values_list("changed_date")[:1]
                )
            )
            .filter(content_changed_date__isnull=False)  # Remove page content with redirects
        )

    def lastmod(self, page_url):
        return page_url.content_changed_date

    def location(self, page_url):
        return page_url.get_absolute_url(page_url.language)

    def get_urls(self, page=1, site=None, protocol=None):
        self.site = site
        return super().get_urls(page, site, protocol)
