import warnings

from django.contrib.sites.models import Site
from django.test import RequestFactory, override_settings

from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase
from cms.utils import get_current_site
from cms.utils.admin import get_site_from_request
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning


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

class GetCurrentSiteTests(CMSTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Stelle sicher, dass eindeutige Sites existieren
        Site.objects.all().delete()
        self.site1 = Site.objects.create(domain='example.com', name='Example')
        self.site2 = Site.objects.create(domain='second.test', name='Second')

    @override_settings(SITE_ID=1)
    def test_request_site_attribute_is_used(self):
        with self.settings(SITE_ID=self.site1.id):
            req = self.factory.get('/')
            # Middleware könnte request.site setzen – simuliere das
            req.site = self.site2
            site = get_current_site(req)
            self.assertEqual(site.pk, self.site2.pk)

    @override_settings(SITE_ID=1)
    def test_warns_without_request_and_returns_current(self):
        with self.settings(SITE_ID=self.site1.id):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                site = get_current_site()
                self.assertTrue(any(issubclass(wi.category, RemovedInDjangoCMS60Warning) for wi in w))
            self.assertEqual(site.pk, self.site1.pk)

    @override_settings(SITE_ID=1)
    def test_fallback_to_default_site(self):
        with self.settings(SITE_ID=self.site1.id):
            req = self.factory.get('/')
            site = get_current_site(req)
            self.assertEqual(site.pk, self.site1.pk)


class GetSiteFromRequestTests(CMSTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        Site.objects.all().delete()
        self.site_default = Site.objects.create(domain='default.test', name='Default')
        self.site_other = Site.objects.create(domain='other.test', name='Other')

    def test_get_param_valid_returns_requested_site(self):
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.get(f'/admin/?site={self.site_other.pk}')
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_other.pk)

    def test_post_param_valid_returns_requested_site(self):
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.post('/admin/', data={'site': str(self.site_other.pk)})
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_other.pk)

    def test_invalid_non_integer_falls_back_to_current_site(self):
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.get('/admin/?site=not-an-int')
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_default.pk)

    def test_nonexistent_site_id_falls_back_to_current_site(self):
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.get('/admin/?site=999999')
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_default.pk)

    def test_missing_param_falls_back_to_current_site(self):
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.get('/admin/')
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_default.pk)


class GetSiteFromRequestWithMiddlewareTests(CMSTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        Site.objects.all().delete()
        self.site_default = Site.objects.create(domain='default.test', name='Default')
        self.site_other = Site.objects.create(domain='other.test', name='Other')

    def test_request_site_from_middleware_is_respected(self):
        """Test that if middleware sets request.site, get_site_from_request respects it."""
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.get('/admin/')
            # Simulate middleware setting request.site
            req.site = self.site_other
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_other.pk)

    def test_request_site_from_middleware_does_not_override_get_param(self):
        """Test that request.site does not override GET parameter."""
        # GET param points to default, but middleware sets other
        req = self.factory.get(f'/admin/?site={self.site_default.pk}')
        req.site = self.site_other
        site = get_site_from_request(req)
        self.assertEqual(site.pk, self.site_default.pk)

    def test_request_site_from_middleware_does_not_override_post_param(self):
        """Test that request.site does not override POST parameter."""
        with self.settings(SITE_ID=self.site_default.pk):
            req = self.factory.post('/admin/', data={'site': str(self.site_other.pk)})
            req.site = self.site_default
            site = get_site_from_request(req)
            self.assertEqual(site.pk, self.site_other.pk)
