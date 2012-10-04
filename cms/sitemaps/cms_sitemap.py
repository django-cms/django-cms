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
        modification_dates = [page.changed_date, page.publication_date]
        plugins_for_placeholder = lambda placeholder: placeholder.cmsplugin_set.all()
        plugins = from_iterable(map(plugins_for_placeholder, page.placeholders.all()))
        plugin_modification_dates = map(lambda plugin: plugin.changed_date, plugins)
        modification_dates.extend(plugin_modification_dates)
        return max(modification_dates)
    
