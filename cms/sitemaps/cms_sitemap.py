# -*- coding: utf-8 -*-
from django.contrib.sitemaps import Sitemap

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
        from cms.utils.moderator import get_page_queryset
        page_queryset = get_page_queryset(None)
        all_pages = page_queryset.published().filter(login_required=False)
        return all_pages

    def lastmod(self, page):
        from cms.models import Placeholder, CMSPlugin
        placeholders_qs = Placeholder.objects.filter(page=page)
        placeholders_ids = list(placeholders_qs.values_list('id', flat=True))
        plugins_qs = CMSPlugin.objects.filter(placeholder__in=placeholders_ids)
        latest_plg_mod_date = plugins_qs.order_by(
            '-changed_date').values_list('changed_date', flat=True)[0]
        return max([
            page.changed_date, page.publication_date, latest_plg_mod_date])

