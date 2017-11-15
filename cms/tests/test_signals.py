# -*- coding: utf-8 -*-
from django.conf import settings
from django.test.utils import override_settings

from cms.api import create_page
from cms.models import Page, UrlconfRevision
from cms.signals import urls_need_reloading
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.util.context_managers import apphooks, signal_tester
from cms.test_utils.testcases import CMSTestCase


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
                        published=True,
                    )
                    redirect_to = self.get_admin_url(Page, 'changelist')
                    endpoint = self.get_admin_url(Page, 'advanced', cms_page.pk)
                    page_data = {
                        "redirect": "",
                        "language": "en",
                        "reverse_id": "",
                        "navigation_extenders": "",
                        "site": "1",
                        "xframe_options": "0",
                        "application_urls": "SampleApp",
                        "application_namespace": "sampleapp",
                        "overwrite_url": "",
                        "template": "INHERIT",
                    }
                    response = self.client.post(endpoint, page_data)
                    self.assertRedirects(response, redirect_to)
                    self.assertEqual(env.call_count, 1)

    def test_urls_need_reloading_signal_delete(self):
        with apphooks(SampleApp):
            with signal_tester(urls_need_reloading) as env:
                self.client.get('/')
                self.assertEqual(env.call_count, 0)
                page = create_page(
                    "apphooked-page",
                    "nav_playground.html",
                    "en",
                    published=True,
                    apphook="SampleApp",
                    apphook_namespace="test"
                )
                page.delete()
                self.client.get('/')
                self.assertEqual(env.call_count, 1)

    def test_urls_need_reloading_signal_change_slug(self):
        superuser = self.get_superuser()
        redirect_to = self.get_admin_url(Page, 'changelist')

        with apphooks(SampleApp):
            with self.login_user_context(superuser):
                with signal_tester(urls_need_reloading) as env:
                    self.assertEqual(env.call_count, 0)
                    page = create_page(
                        "apphooked-page",
                        "nav_playground.html",
                        "en",
                        published=True,
                        apphook="SampleApp",
                        apphook_namespace="test"
                    )
                    # Change slug
                    endpoint = self.get_admin_url(Page, 'change', page.pk)
                    page_data = {
                        'title': 'apphooked-page',
                        'slug': 'apphooked-page-2',
                    }
                    response = self.client.post(endpoint, page_data)
                    self.assertRedirects(response, redirect_to)
                    # Publish should trigger the signal
                    endpoint = self.get_admin_url(Page, 'publish_page', page.pk, 'en')
                    self.client.post(endpoint)
                    self.assertEqual(env.call_count, 1)


overrides = dict()
overrides['MIDDLEWARE' if getattr(settings, 'MIDDLEWARE', None) else 'MIDDLEWARE_CLASSES'] = [
    'cms.middleware.utils.ApphookReloadMiddleware'
] + getattr(settings, 'MIDDLEWARE', getattr(settings, 'MIDDLEWARE_CLASSES', None))
@override_settings(**overrides)
class ApphooksReloadTests(CMSTestCase):
    def test_urls_reloaded(self):
        """
        Tests that URLs are automatically reloaded when the ApphookReload
        middleware is installed.
        """
        #
        # Sets up an apphook'ed page, but does not yet publish it.
        #
        superuser = self.get_superuser()
        page = create_page("home", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        app_page = create_page("app_page", "nav_playground.html", "en",
                               created_by=superuser, parent=page,
                               published=False, apphook="SampleApp")
        self.client.get('/')  # Required to invoke the middleware
        #
        # Gets the current urls revision for testing against later.
        #
        current_revision, _ = UrlconfRevision.get_or_create_revision()

        #
        # Publishes the apphook. This is one of many ways to trigger the
        # firing of the signal. The tests above test some of the other ways
        # already.
        endpoint = self.get_admin_url(Page, 'publish_page', app_page.pk, 'en')

        with self.login_user_context(superuser):
            self.client.post(endpoint)
        self.client.get('/')  # Required to invoke the middleware

        # And, this should result in a the updating of the UrlconfRevision
        new_revision, _ = UrlconfRevision.get_or_create_revision()
        self.assertNotEquals(current_revision, new_revision)
