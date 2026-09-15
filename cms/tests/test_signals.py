import warnings
from unittest.mock import patch

from django.conf import settings
from django.test.utils import override_settings

from cms.api import create_page
from cms.cache import _get_cache_version
from cms.models import Page, UrlconfRevision
from cms.shared.signals import page_caches_invalidated, placeholder_cache_cleared
from cms.signals import move_page, urls_need_reloading
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import apphooks, signal_tester
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from menus.menu_pool import menu_pool

overrides = {
    'MIDDLEWARE': ['cms.middleware.utils.ApphookReloadMiddleware'] + settings.MIDDLEWARE,
    'CMS_PERMISSION': False,
}


@override_settings(**overrides)
class SignalTests(CMSTestCase):
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


class CrossContainerCacheSignalTests(CMSTestCase):
    """The model layer announces cache invalidation; receivers act on it.

    These replaced two import cycles -- ``cms.models.pagemodel`` calling
    ``menus.menu_pool`` and ``cms.models.placeholdermodel`` calling the page
    cache. If a receiver silently stops being connected, nothing raises; caches
    just go stale. Hence these tests.
    """

    def test_receivers_are_connected(self):
        # Matched on dispatch_uid rather than on the receiver object: the shape
        # of Signal.receivers entries is a Django implementation detail and has
        # changed between versions, but the lookup key's first element is the
        # dispatch_uid we connect with.
        self.assertIn(
            "cms_invalidate_page_cache_for_placeholder",
            [key[0] for key, *_ in placeholder_cache_cleared.receivers],
        )
        self.assertIn(
            "cms_clear_menu_cache_for_page",
            [key[0] for key, *_ in page_caches_invalidated.receivers],
        )

    @override_settings(CMS_PAGE_CACHE=True)
    def test_clearing_a_placeholder_cache_invalidates_the_page_cache(self):
        page = create_page("home", "nav_playground.html", "en")
        placeholder = page.get_placeholders("en").first()

        before = _get_cache_version()
        placeholder.clear_cache("en")

        self.assertGreater(_get_cache_version(), before)

    @override_settings(CMS_PAGE_CACHE=False)
    def test_page_cache_is_left_alone_when_disabled(self):
        page = create_page("home", "nav_playground.html", "en")
        placeholder = page.get_placeholders("en").first()

        before = _get_cache_version()
        placeholder.clear_cache("en")

        self.assertEqual(_get_cache_version(), before)

    def test_menu_cache_is_cleared_only_when_the_caller_asks(self):
        page = create_page("home", "nav_playground.html", "en")

        with patch.object(menu_pool, "clear") as clear:
            page.clear_cache(menu=False)
        clear.assert_not_called()

        with patch.object(menu_pool, "clear") as clear:
            page.clear_cache(menu=True)
        clear.assert_called_once_with(site_id=page.site_id)
