# -*- coding: utf-8 -*-

from django.contrib.sitemaps import Sitemap
from django.db.models import Q
from django.utils import translation

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
        all_titles = Title.objects.public().filter(
            Q(redirect='') | Q(redirect__isnull=True),
            page__login_required=False
        )
        return all_titles

    def lastmod(self, title):
        modification_dates = [title.page.changed_date, title.page.publication_date]
        plugins_for_placeholder = lambda placeholder: placeholder.get_plugins()
        plugins = from_iterable(map(plugins_for_placeholder, title.page.placeholders.all()))
        plugin_modification_dates = map(lambda plugin: plugin.changed_date, plugins)
        modification_dates.extend(plugin_modification_dates)
        return max(modification_dates)

    def location(self, title):
        translation.activate(title.language)
        url = title.page.get_absolute_url(title.language)
        translation.deactivate()
        return url
