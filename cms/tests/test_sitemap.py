import copy

from cms.api import create_page, create_page_content
from cms.models import PageUrl
from cms.sitemaps import CMSSitemap
from cms.test_utils.testcases import CMSTestCase
from cms.utils.compat import DJANGO_4_2
from cms.utils.conf import get_cms_setting

protocol = "http" if DJANGO_4_2 else "https"

class SitemapTestCase(CMSTestCase):
    def setUp(self):
        """
        Tree from fixture:

            + P1 (de, en)
            | + P2 (de, en)
            |   + P3 (de, en)
            | + P9 (de unpublished, en)
            |   + P10 unpublished (de, en)
            |   + P11 (en)
            + P4 (de, en)
            | + P5 (de, en)
            + P6 (de, en) (not in menu)
              + P7 (de, en)
              + P8 (de, en)
        """
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',
        }
        with self.settings(CMS_PERMISSION=False):
            p1 = create_page('P1', in_navigation=True, **defaults)
            create_page_content(language='de', title="other title %s" % p1.get_title('en'), page=p1)

            p4 = create_page('P4', in_navigation=True, **defaults)
            create_page_content(language='de', title="other title %s" % p4.get_title('en'), page=p4)

            p6 = create_page('P6', in_navigation=False, **defaults)
            create_page_content(language='de', title="other title %s" % p6.get_title('en'), page=p6)

            p2 = create_page('P2', in_navigation=True, parent=p1, **defaults)
            create_page_content(language='de', title="other title %s" % p2.get_title('en'), page=p2)

            p3 = create_page('P3', in_navigation=True, parent=p2, **defaults)
            create_page_content(language='de', title="other title %s" % p3.get_title('en'), page=p3)

            p5 = create_page('P5', in_navigation=True, parent=p4, **defaults)
            create_page_content(language='de', title="other title %s" % p5.get_title('en'), page=p5)

            p7 = create_page('P7', in_navigation=True, parent=p6, **defaults)
            create_page_content(language='de', title="other title %s" % p7.get_title('en'), page=p7)

            p8 = create_page('P8', in_navigation=True, parent=p6, **defaults)
            create_page_content(language='de', title="other title %s" % p8.get_title('en'), page=p8)

            p9 = create_page('P9', in_navigation=True, parent=p1, **defaults)
            create_page_content(language='de', title="other title %s" % p9.get_title('en'), page=p9)

            p10 = create_page('P10', in_navigation=True, parent=p9, **defaults)
            create_page_content(language='de', title="other title %s" % p10.get_title('en'), page=p10)

            create_page('P11', in_navigation=True, parent=p9, **defaults)

    def test_sitemap_count(self):
        """
        Has the sitemap the correct number of elements?
        """
        sitemap = CMSSitemap()
        self.assertEqual(len(sitemap.items()), 21)

    def test_sitemap_items_location(self):
        """
        Check the correct URL in location, recreating it according to the title
        attributes (instead of using Page.get_absolute_url) for a lower level
        check
        """
        sitemap = CMSSitemap()
        urlset = sitemap.get_urls()
        for item in urlset:
            if item['item'].path:
                url = f'{protocol}://example.com/{item["item"].language}/{item["item"].path}/'
            else:
                url = f'{protocol}://example.com/{item["item"].language}/'
            self.assertEqual(item['location'], url)

    def test_sitemap_urls(self):
        """
        Check that published titles are in the urls
        """
        sitemap = CMSSitemap()
        locations = []
        urlset = sitemap.get_urls()
        for item in urlset:
            locations.append(item['location'])
        for page_url in PageUrl.objects.all():
            if page_url.path:
                url = f'{protocol}://example.com/{page_url.language}/{page_url.path}/'
            else:
                url = f'{protocol}://example.com/{page_url.language}/'
            self.assertTrue(url in locations)

    def test_sitemap_uses_public_languages_only(self):
        """
        Pages on the sitemap should only show public languages.
        """
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        # sanity check
        assert lang_settings[1][1]['code'] == 'de'
        # set german as private
        lang_settings[1][1]['public'] = False

        with self.settings(CMS_LANGUAGES=lang_settings):
            for item in CMSSitemap().get_urls():
                url = f'{protocol}://example.com/en/'

                if item['item'].path:
                    url += item['item'].path + '/'
                self.assertEqual(item['location'], url)
