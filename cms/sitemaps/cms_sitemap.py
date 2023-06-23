from collections import defaultdict

from django.contrib.sitemaps import Sitemap
from django.db.models import OuterRef, Q, Subquery

from cms.models import PageContent, PageUrl
from cms.utils import get_current_site
from cms.utils.i18n import get_public_languages


def from_iterable(iterables):
    """
    Backport of itertools.chain.from_iterable
    """
    for it in iterables:
        for element in it:
            yield element


class CMSSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
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
        site = get_current_site()
        languages = get_public_languages(site_id=site.pk)

        included_contents= (
            PageContent
            .objects
            .filter(language__in=languages, page__node__site=site, page__login_required=False)
            .filter(Q(redirect='') | Q(redirect__isnull=True))
            .order_by('page__node__path')
            .annotate(url=Subquery(PageUrl.objects.filter(language=OuterRef("language"), path__isnull=False))[:1])
        )

        return [page_content.url for page_content in included_contents if page_content.url]

    def lastmod(self, page_url):
        return page_url.page.changed_date

    def location(self, page_url):
        return page_url.get_absolute_url(page_url.language)
