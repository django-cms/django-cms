import copy

from cms.api import create_page, create_title
from cms.models import Page, Title
from cms.sitemaps import CMSSitemap
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import get_cms_setting


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
            p1 = create_page('P1', published=True, in_navigation=True, **defaults)
            create_title(language='de', title="other title %s" % p1.get_title('en'), page=p1)

            p4 = create_page('P4', published=True, in_navigation=True, **defaults)
            create_title(language='de', title="other title %s" % p4.get_title('en'), page=p4)

            p6 = create_page('P6', published=True, in_navigation=False, **defaults)
            create_title(language='de', title="other title %s" % p6.get_title('en'), page=p6)

            p2 = create_page('P2', published=True, in_navigation=True, parent=p1, **defaults)
            create_title(language='de', title="other title %s" % p2.get_title('en'), page=p2)

            p3 = create_page('P3', published=True, in_navigation=True, parent=p2, **defaults)
            create_title(language='de', title="other title %s" % p3.get_title('en'), page=p3)

            p5 = create_page('P5', published=True, in_navigation=True, parent=p4, **defaults)
            create_title(language='de', title="other title %s" % p5.get_title('en'), page=p5)

            p7 = create_page('P7', published=True, in_navigation=True, parent=p6, **defaults)
            create_title(language='de', title="other title %s" % p7.get_title('en'), page=p7)

            p8 = create_page('P8', published=True, in_navigation=True, parent=p6, **defaults)
            create_title(language='de', title="other title %s" % p8.get_title('en'), page=p8)

            p9 = create_page('P9', published=True, in_navigation=True, parent=p1, **defaults)
            create_title(language='de', title="other title %s" % p9.get_title('en'), page=p9)

            p10 = create_page('P10', published=False, in_navigation=True, parent=p9, **defaults)
            create_title(language='de', title="other title %s" % p10.get_title('en'), page=p10)

            create_page('P11', published=True, in_navigation=True, parent=p9, **defaults)

            p1.reload().publish('de')
            p2.reload().publish('de')
            p3.reload().publish('de')
            p4.reload().publish('de')
            p5.reload().publish('de')
            p6.reload().publish('de')
            p7.reload().publish('de')
            p8.reload().publish('de')
            self.assertEqual(Title.objects.filter(published=True, publisher_is_draft=False).count(), 18)


    def test_sitemap_count(self):
        """
        Has the sitemap the correct number of elements?
        """
        sitemap = CMSSitemap()
        # 8 pages with en and de titles published
        # 1 page published only in english(with existsing de title)
        # 1 page with both titles but unpublished
        # 1 page with only english title
        self.assertEqual(sitemap.items().count(), 18)

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
                url = 'http://example.com/%s/%s/' % (item['item'].language, item['item'].path)
            else:
                url = 'http://example.com/%s/%s' % (item['item'].language, item['item'].path)
            self.assertEqual(item['location'], url)

    def test_sitemap_published_titles(self):
        """
        Check that published titles are in the urls
        """
        sitemap = CMSSitemap()
        locations = []
        urlset = sitemap.get_urls()
        for item in urlset:
            locations.append(item['location'])
        for title in Title.objects.public():
            page = title.page.get_public_object()
            if title.path:
                url = 'http://example.com/%s/%s/' % (title.language, title.path)
            else:
                url = 'http://example.com/%s/%s' % (title.language, title.path)
            if page.is_published('en') and not page.publisher_is_draft:
                self.assertTrue(url in locations)
            else:
                self.assertFalse(url in locations)

    def test_sitemap_unpublished_titles(self):
        """
        Check that titles attached to unpublished pages are not in the urlset.
        As titles are 'published' depending on their attached page, we create a
        set of unpublished titles by checking titles attached to the draft and
        public version of each page
        """
        sitemap = CMSSitemap()
        locations = []
        urlset = sitemap.get_urls()
        unpublished_titles = set()
        for item in urlset:
            locations.append(item['location'])
        for page in Page.objects.drafts():
            if page.get_public_object():
                set1 = set(page.get_public_object().title_set.values_list('path', flat=True))
                set2 = set(page.title_set.values_list('path', flat=True))
                unpublished_titles.update(set2.difference(set1))
            else:
                unpublished_titles.update(page.title_set.values_list('path', flat=True))

        for path in unpublished_titles:
            title = Title.objects.get(path=path)
            if title.path:
                url = 'http://example.com/%s/%s/' % (title.language, title.path)
            else:
                url = 'http://example.com/%s/%s' % (title.language, title.path)
            self.assertFalse(url in locations)

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
                url = 'http://example.com/en/'

                if item['item'].path:
                    url += item['item'].path + '/'
                self.assertEqual(item['location'], url)
