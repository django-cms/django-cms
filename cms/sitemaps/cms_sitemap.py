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
        modification_dates = [page.changed_date, page.publication_date]
        return max(modification_dates)
    
