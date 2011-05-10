# -*- coding: utf-8 -*-
from django.contrib.sitemaps import Sitemap

class CMSSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        from cms.utils.moderator import get_page_queryset
        page_queryset = get_page_queryset(None)
        all_pages = page_queryset.published().filter(login_required=False)
        return all_pages

    def lastmod(self, page):
        return page.publication_date or page.creation_date
    
