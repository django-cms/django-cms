# -*- coding: utf-8 -*-
import copy

from django.contrib.sites.models import Site

from cms.api import create_page
from cms.models import Page, Placeholder
from cms.test_utils.testcases import CMSTestCase, URL_CMS_PAGE
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse


class SiteTestCase(CMSTestCase):
    """Site framework specific test cases.

    All stuff which is changing settings.SITE_ID for tests should come here.
    """

    def setUp(self):
        self.assertEqual(Site.objects.all().count(), 1)
        with self.settings(SITE_ID=1):
            u = self._create_user("test", True, True)

            # setup sites
            self.site2 = Site.objects.create(domain="sample2.com", name="sample2.com", pk=2)
            self.site3 = Site.objects.create(domain="sample3.com", name="sample3.com", pk=3)

        self._login_context = self.login_user_context(u)
        self._login_context.__enter__()

    def tearDown(self):
        self._login_context.__exit__(None, None, None)

    def test_site_framework(self):
        #Test the site framework, and test if it's possible to disable it
        with self.settings(SITE_ID=self.site2.pk):
            create_page("page_2a", "nav_playground.html", "de", site=self.site2)

            response = self.client.get("%s?site__exact=%s" % (URL_CMS_PAGE, self.site3.pk))
            self.assertEqual(response.status_code, 200)
            create_page("page_3b", "nav_playground.html", "de", site=self.site3)

        with self.settings(SITE_ID=self.site3.pk):
            create_page("page_3a", "nav_playground.html", "nl", site=self.site3)

            # with param
            self.assertEqual(Page.objects.on_site(self.site2.pk).count(), 1)
            self.assertEqual(Page.objects.on_site(self.site3.pk).count(), 2)

            self.assertEqual(Page.objects.drafts().on_site().count(), 2)

        with self.settings(SITE_ID=self.site2.pk):
            # without param
            self.assertEqual(Page.objects.drafts().on_site().count(), 1)

    def test_site_preview(self):
        page = create_page("page", "nav_playground.html", "de", site=self.site2, published=True)
        page_edit_url_on = self.get_edit_on_url(page.get_absolute_url('de'))

        with self.login_user_context(self.get_superuser()):
            # set the current site on changelist
            response = self.client.post(admin_reverse('cms_page_changelist'), {'site': self.site2.pk})
            self.assertEqual(response.status_code, 200)
            # simulate user clicks on preview icon
            response = self.client.get(admin_reverse('cms_page_preview_page', args=[page.pk, 'de']))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response._headers['location'][1], 'http://sample2.com{}&language=de'.format(page_edit_url_on))

    def test_site_publish(self):
        self._login_context.__exit__(None, None, None)
        pages = {"2": list(range(0, 5)), "3": list(range(0, 5))}
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[3][1]['public'] = True

        with self.settings(CMS_LANGUAGES=lang_settings, LANGUAGE_CODE="de"):
            with self.settings(SITE_ID=self.site2.pk):
                pages["2"][0] = create_page("page_2", "nav_playground.html", "de",
                                            site=self.site2, published=True)
                pages["2"][1] = create_page("page_2_1", "nav_playground.html", "de",
                                            parent=pages["2"][0], site=self.site2, published=True)
                pages["2"][2] = create_page("page_2_2", "nav_playground.html", "de",
                                            parent=pages["2"][0], site=self.site2, published=True)
                pages["2"][3] = create_page("page_2_1_1", "nav_playground.html", "de",
                                            parent=pages["2"][1], site=self.site2, published=True)
                pages["2"][4] = create_page("page_2_1_2", "nav_playground.html", "de",
                                            parent=pages["2"][1], site=self.site2, published=True)

                for page in pages["2"]:
                    page_url = page.get_absolute_url(language='de')
                    response = self.client.get(page_url)
                    self.assertEqual(response.status_code, 200)

            with self.settings(SITE_ID=self.site3.pk):
                pages["3"][0] = create_page("page_3", "nav_playground.html", "de",
                                            site=self.site3)
                pages["3"][0].publish('de')
                pages["3"][1] = create_page("page_3_1", "nav_playground.html", "de",
                                            parent=pages["3"][0], site=self.site3, published=True)
                pages["3"][2] = create_page("page_3_2", "nav_playground.html", "de",
                                            parent=pages["3"][0], site=self.site3, published=True)
                pages["3"][3] = create_page("page_3_1_1", "nav_playground.html", "de",
                                            parent=pages["3"][1], site=self.site3, published=True)
                pages["3"][4] = create_page("page_3_1_2", "nav_playground.html", "de",
                                            parent=pages["3"][1], site=self.site3, published=True)

                for page in pages["3"]:
                    if page.is_home:
                        page_url = "/de/"
                    else:
                        page_url = page.get_absolute_url(language='de')
                    response = self.client.get(page_url)
                    self.assertEqual(response.status_code, 200)

    def test_site_delete(self):
        with self.settings(SITE_ID=self.site2.pk):
            create_page("page_2a", "nav_playground.html", "de", site=self.site2)
            self.assertEqual(Placeholder.objects.count(), 2)
            self.site2.delete()
            self.assertEqual(Placeholder.objects.count(), 0)
