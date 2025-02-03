from django.contrib.sites.models import Site

from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase


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
        # Test the site framework, and test if it's possible to disable it
        with self.settings(SITE_ID=self.site2.pk):
            create_page("page_2a", "nav_playground.html", "de", site=self.site2)
            page_list = self.get_pages_admin_list_uri('en')
            response = self.client.get(f"{page_list}?site__exact={self.site3.pk}")
            self.assertEqual(response.status_code, 200)
            create_page("page_3b", "nav_playground.html", "de", site=self.site3)

        with self.settings(SITE_ID=self.site3.pk):
            create_page("page_3a", "nav_playground.html", "nl", site=self.site3)

            # with param
            self.assertEqual(Page.objects.on_site(self.site2.pk).count(), 1)
            self.assertEqual(Page.objects.on_site(self.site3.pk).count(), 2)

            self.assertEqual(Page.objects.on_site().count(), 2)

        with self.settings(SITE_ID=self.site2.pk):
            # without param
            self.assertEqual(Page.objects.on_site().count(), 1)
