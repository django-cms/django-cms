# -*- coding: utf-8 -*-
from django.contrib.sitemaps import Sitemap
from django.utils.translation import get_language
from cms.models import Title

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
        titles = Title.objects.public().filter(page__login_required=False, \
                    language=get_language())
        return titles

    def lastmod(self, title):
        page = title.page
        modification_dates = [page.changed_date, page.publication_date]
        plugins_for_placeholder = lambda placeholder: placeholder.get_plugins()
        plugins = from_iterable(map(plugins_for_placeholder, page.placeholders.all()))
        plugin_modification_dates = map(lambda plugin: plugin.changed_date, plugins)
        modification_dates.extend(plugin_modification_dates)
        return max(modification_dates)

    def location(self, title):
        return title.page.get_absolute_url()
