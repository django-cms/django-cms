import warnings

from django.conf import settings
from django.core.signals import request_finished
from django.test.utils import override_settings

from cms.api import create_page
from cms.models import Page, UrlconfRevision
from cms.signals import move_page, urls_need_reloading
from cms.signals.apphook import DISPATCH_UID
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import apphooks, signal_tester
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning

overrides = {
    'MIDDLEWARE': ['cms.middleware.utils.ApphookReloadMiddleware'] + settings.MIDDLEWARE,
    'CMS_PERMISSION': False,
}


@override_settings(**overrides)
class SignalTests(CMSTestCase):
    def _discard_pending_reload(self):
        # Creating a page with an apphook outside of a request schedules a reload
        # for the end of the next request, which would be credited to the operation
        # under test
        request_finished.disconnect(dispatch_uid=DISPATCH_UID)

    def _move_page(self, page, target, position=0):
        endpoint = self.get_admin_url(Page, 'move_page', page.pk)
        response = self.client.post(endpoint, {'id': page.pk, 'position': position, 'target': target.pk})
        # The endpoint reports the outcome of the move in its JSON payload
        self.assertEqual(response.json()['status'], 200)

    def test_move_page_signal_warns_on_connect(self):
        def receiver(**kwargs):
            return None

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RemovedInDjangoCMS60Warning)
            move_page.connect(receiver)

        self.assertTrue(
            any(issubclass(warning.category, RemovedInDjangoCMS60Warning) for warning in caught),
            "Expected deprecation warning when connecting to move_page signal.",
        )

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
                    redirect_to = self.get_pages_admin_list_uri(site_id=cms_page.site_id)
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
                self._discard_pending_reload()

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

    def test_urls_need_reloading_signal_delete_ancestor(self):
        parent = create_page("parent", "nav_playground.html", "en")
        create_page("apphooked-page", "nav_playground.html", "en", parent=parent, apphook="SampleApp")
        self._discard_pending_reload()

        with self.login_user_context(self.get_superuser()):
            with signal_tester(urls_need_reloading) as env:
                current_revision, _ = UrlconfRevision.get_or_create_revision()
                self.client.post(self.get_admin_url(Page, 'delete', parent.pk), {'post': 'yes'})
                # The apphooked page is deleted along with its parent
                self.assertFalse(Page.objects.exists())
                self.assertEqual(env.call_count, 1)
                new_revision, _ = UrlconfRevision.get_or_create_revision()
                self.assertNotEqual(current_revision, new_revision)

    def test_urls_need_reloading_signal_move_ancestor(self):
        parent_1 = create_page("parent-1", "nav_playground.html", "en")
        parent_2 = create_page("parent-2", "nav_playground.html", "en")
        page = create_page("apphooked-page", "nav_playground.html", "en", parent=parent_1, apphook="SampleApp")
        self._discard_pending_reload()

        with self.login_user_context(self.get_superuser()):
            with signal_tester(urls_need_reloading) as env:
                current_revision, _ = UrlconfRevision.get_or_create_revision()
                self._move_page(parent_1, parent_2)
                self.assertEqual(page.urls.get(language="en").path, "parent-2/parent-1/apphooked-page")
                self.assertEqual(env.call_count, 1)
                new_revision, _ = UrlconfRevision.get_or_create_revision()
                self.assertNotEqual(current_revision, new_revision)

    def test_no_urls_need_reloading_signal_move_unchanged_url(self):
        home = create_page("home", "nav_playground.html", "en")
        home.set_as_homepage()
        page = create_page("apphooked-page", "nav_playground.html", "en", apphook="SampleApp")
        self._discard_pending_reload()

        with self.login_user_context(self.get_superuser()):
            with signal_tester(urls_need_reloading) as env:
                # The page gets a new parent, but children of the home page live at
                # the root: its url does not change
                self._move_page(page, home)
                self.assertEqual(Page.objects.get(pk=page.pk).parent, home)
                self.assertEqual(page.urls.get(language="en").path, "apphooked-page")
                self.assertEqual(env.call_count, 0)

    def test_no_urls_need_reloading_signal_without_apphook(self):
        # Only a page outside of the moved and deleted subtree has an apphook
        create_page("apphooked-page", "nav_playground.html", "en", apphook="SampleApp")
        parent_1 = create_page("parent-1", "nav_playground.html", "en")
        parent_2 = create_page("parent-2", "nav_playground.html", "en")
        page = create_page("page", "nav_playground.html", "en", parent=parent_1)
        self._discard_pending_reload()

        with self.login_user_context(self.get_superuser()):
            with signal_tester(urls_need_reloading) as env:
                self._move_page(page, parent_2)
                self.assertEqual(page.urls.get(language="en").path, "parent-2/page")
                self.client.post(self.get_admin_url(Page, 'delete', parent_2.pk), {'post': 'yes'})
                self.assertEqual(Page.objects.count(), 2)
                self.assertEqual(env.call_count, 0)
