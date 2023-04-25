
from django.contrib.sitemaps import Sitemap
from django.db.models import Q
from django.utils import translation

from cms.models import Title
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
        # If, for some reason, you require redirecting pages (Titles) to be
        # included, simply create a new class inheriting from this one, and
        # supply a new items() method which doesn't filter out the redirects.
        site = get_current_site()
        languages = get_public_languages(site_id=site.pk)
        all_titles = Title.objects.public().filter(
            Q(redirect='') | Q(redirect__isnull=True),
            language__in=languages,
            page__login_required=False,
            page__node__site=site,
        ).order_by('page__node__path')
        return all_titles

    def lastmod(self, title):
        modification_dates = [title.page.changed_date, title.page.publication_date]
        def plugins_for_placeholder(placeholder):
            return placeholder.get_plugins()
        plugins = from_iterable(map(plugins_for_placeholder, title.page.placeholders.all()))
        plugin_modification_dates = (plugin.changed_date for plugin in plugins)
        modification_dates.extend(plugin_modification_dates)
        return max(modification_dates)

    def location(self, title):
        translation.activate(title.language)
        url = title.page.get_absolute_url(title.language)
        translation.deactivate()
        return url
