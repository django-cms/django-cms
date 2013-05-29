# -*- coding: utf-8 -*-
from __future__ import with_statement
import copy
from django.test import Client
from cms.api import create_page
from cms.models import Page
from cms.utils import get_cms_setting
from cms.views import details
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

class SiteTestCase(CMSTestCase):
    """Site framework specific test cases.
    
    All stuff which is changing settings.SITE_ID for tests should come here.
    """
    def setUp(self):
        self.assertEqual(Site.objects.all().count(), 1)
        with SettingsOverride(SITE_ID=1):

            u = User(username="test", is_staff=True, is_active=True, is_superuser=True)
            u.set_password("test")
            u.save()

            # setup sites
            self.site2 = Site.objects.create(domain="sample2.com", name="sample2.com", pk=2)
            self.site3 = Site.objects.create(domain="sample3.com", name="sample3.com", pk=3)

        self._login_context = self.login_user_context(u)
        self._login_context.__enter__()

    def tearDown(self):
        self._login_context.__exit__(None, None, None)


    def test_site_framework(self):
        #Test the site framework, and test if it's possible to disable it
        with SettingsOverride(SITE_ID=self.site2.pk):
            create_page("page_2a", "nav_playground.html", "de", site=self.site2)

            response = self.client.get("/en/admin/cms/page/?site__exact=%s" % self.site3.pk)
            self.assertEqual(response.status_code, 200)
            create_page("page_3b", "nav_playground.html", "de", site=self.site3)

        with SettingsOverride(SITE_ID=self.site3.pk):
            create_page("page_3a", "nav_playground.html", "nl", site=self.site3)

            # with param
            self.assertEqual(Page.objects.on_site(self.site2.pk).count(), 1)
            self.assertEqual(Page.objects.on_site(self.site3.pk).count(), 2)

            self.assertEqual(Page.objects.drafts().on_site().count(), 2)

        with SettingsOverride(SITE_ID=self.site2.pk):
            # without param
            self.assertEqual(Page.objects.drafts().on_site().count(), 1)

    def test_site_publish(self):
        self._login_context.__exit__(None, None, None)
        pages = {"2": range(0, 5), "3": range(0, 5)}
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[3][1]['public'] = True

        with SettingsOverride(CMS_LANGUAGES=lang_settings, LANGUAGE_CODE="de"):
            with SettingsOverride(SITE_ID=self.site2.pk):
                pages["2"][0] = create_page("page_2", "nav_playground.html", "de",
                                            site=self.site2)
                pages["2"][0].publish()
                pages["2"][1] = create_page("page_2_1", "nav_playground.html", "de",
                                            parent=pages["2"][0], site=self.site2)
                pages["2"][2] = create_page("page_2_2", "nav_playground.html", "de",
                                            parent=pages["2"][0], site=self.site2)
                pages["2"][3] = create_page("page_2_1_1", "nav_playground.html", "de",
                                            parent=pages["2"][1], site=self.site2)
                pages["2"][4] = create_page("page_2_1_2", "nav_playground.html", "de",
                                            parent=pages["2"][1], site=self.site2)

                for page in pages["2"]:
                    page.publish()
                for page in pages["2"]:
                    if page.is_home():
                        page_url = "/de/"
                    else:
                        page_url = page.get_absolute_url(language='de')
                    response = self.client.get(page_url)
                    self.assertEqual(response.status_code, 200)

            with SettingsOverride(SITE_ID=self.site3.pk):
                pages["3"][0] = create_page("page_3", "nav_playground.html", "de",
                                            site=self.site3)
                pages["3"][0].publish()
                pages["3"][1] = create_page("page_3_1", "nav_playground.html", "de",
                                            parent=pages["3"][0], site=self.site3)
                pages["3"][2] = create_page("page_3_2", "nav_playground.html", "de",
                                            parent=pages["3"][0], site=self.site3)
                pages["3"][3] = create_page("page_3_1_1", "nav_playground.html", "de",
                                            parent=pages["3"][1], site=self.site3)
                pages["3"][4] = create_page("page_3_1_2", "nav_playground.html", "de",
                                            parent=pages["3"][1], site=self.site3)

                for page in pages["3"]:
                    page.publish()
                for page in pages["3"]:
                    if page.is_home():
                        page_url = "/de/"
                    else:
                        page_url = page.get_absolute_url(language='de')
                    response = self.client.get(page_url)
                    self.assertEqual(response.status_code, 200)