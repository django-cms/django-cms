from django.conf import settings
from django.test.utils import override_settings

from cms.api import create_page
from cms.models import Page, UrlconfRevision
from cms.signals import urls_need_reloading
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import apphooks, signal_tester

overrides = {
    'MIDDLEWARE': ['cms.middleware.utils.ApphookReloadMiddleware'] + settings.MIDDLEWARE,
    'CMS_PERMISSION': False,
}


@override_settings(**overrides)
class SignalTests(CMSTestCase):
    def test_urls_need_reloading_signal_set_apphook(self):
        superuser = self.get_superuser()

        with apphooks(SampleApp):
            with self.login_user_context(superuser):
                with signal_tester(urls_need_reloading) as env:
                    self.assertEqual(env.call_count, 0)
                    cms_page = create_page(
                        "apphooked-page",
                        "nav_playground.html",
                        "en",
                    )
                    redirect_to = self.get_pages_admin_list_uri()
                    endpoint = self.get_admin_url(Page, 'advanced', cms_page.pk)
                    current_revision, _ = UrlconfRevision.get_or_create_revision()
                    page_data = {
                        "reverse_id": "",
                        "navigation_extenders": "",
                        "application_urls": "SampleApp",
                        "application_namespace": "sampleapp",
                    }
                    response = self.client.post(endpoint, page_data)
                    self.assertRedirects(response, redirect_to)
                    self.assertEqual(env.call_count, 1)
                    new_revision, _ = UrlconfRevision.get_or_create_revision()
                    self.assertNotEqual(current_revision, new_revision)

    def test_urls_need_reloading_signal_delete(self):
        superuser = self.get_superuser()

        with apphooks(SampleApp):
            with self.login_user_context(superuser):
                page = create_page(
                    "apphooked-page",
                    "nav_playground.html",
                    "en",
                    apphook="SampleApp",
                    apphook_namespace="test"
                )

                with signal_tester(urls_need_reloading) as env:
                    endpoint = self.get_admin_url(Page, 'delete', page.pk)
                    current_revision, _ = UrlconfRevision.get_or_create_revision()
                    self.assertEqual(env.call_count, 0)
                    self.client.post(endpoint, {'post': 'yes'})
                    self.assertEqual(env.call_count, 1)
                    new_revision, _ = UrlconfRevision.get_or_create_revision()
                    self.assertNotEqual(current_revision, new_revision)

    def test_urls_need_reloading_signal_change_slug(self):
        superuser = self.get_superuser()
        redirect_to = self.get_pages_admin_list_uri()

        with apphooks(SampleApp):
            with self.login_user_context(superuser):
                with signal_tester(urls_need_reloading) as env:
                    current_revision, _ = UrlconfRevision.get_or_create_revision()
                    self.assertEqual(env.call_count, 0)
                    page = create_page(
                        "apphooked-page",
                        "nav_playground.html",
                        "en",
                        apphook="SampleApp",
                        apphook_namespace="test"
                    )
                    # Change slug should trigger the signal
                    endpoint = self.get_page_change_uri('en', page)
                    page_data = {
                        'title': 'apphooked-page',
                        'slug': 'apphooked-page-2',
                        'template': 'nav_playground.html'
                    }
                    response = self.client.post(endpoint, page_data)
                    self.assertRedirects(response, redirect_to)
                    self.assertEqual(env.call_count, 1)
                    new_revision, _ = UrlconfRevision.get_or_create_revision()
                    self.assertNotEqual(current_revision, new_revision)
