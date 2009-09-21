from django.contrib.sitemaps import Sitemap
from cms.utils.moderator import get_page_queryset
from cms.models import Page

class CMSSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        page_queryset = get_page_queryset(None)
        all_pages = page_queryset.published()
        return all_pages

    def lastmod(self, page):
        return page.publication_date or page.creation_date
    