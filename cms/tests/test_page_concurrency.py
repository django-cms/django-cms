"""Separate-connection coverage for validation and writes under the site lock."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature

from cms.api import create_page, create_page_content
from cms.models import Page, PageContent, PageUrl
from cms.pages import services
from cms.shared.operations import OperationContext


@skipUnlessDBFeature("has_select_for_update")
class PageConcurrencyTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        user_model = get_user_model()
        user = user_model.objects.create(**{user_model.USERNAME_FIELD: "concurrency@example.com"})
        self.context = OperationContext.system("concurrency test", user=user)
        Site.objects.clear_cache()
        self.site = Site.objects.get_current()
        self.parent = create_page("Parent", "nav_playground.html", "en", site=self.site)
        self.other = create_page("Other", "nav_playground.html", "en", site=self.site)

    def overlap(self, first, second):
        """Hold the first write uncommitted while the second tries to lock."""
        written, release, locking, done = (Event() for _ in range(4))

        def write_first():
            try:
                with transaction.atomic():
                    result = first()
                    written.set()
                    if not release.wait(10):
                        raise AssertionError("Timed out waiting to commit the first write")
                return result
            finally:
                connections.close_all()

        def observe_lock(execute, sql, params, many, context):
            if "django_site" in sql and "FOR UPDATE" in sql:
                locking.set()
            return execute(sql, params, many, context)

        def write_second():
            try:
                with connection.execute_wrapper(observe_lock):
                    return second()
            finally:
                done.set()
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first_result = pool.submit(write_first)
            try:
                if not written.wait(10):
                    first_result.result(timeout=1)
                    self.fail("First write never completed")
                second_result = pool.submit(write_second)
                self.assertTrue(locking.wait(10), "Second write never tried to acquire the site lock")
                self.assertFalse(done.wait(0.1), "Second write did not wait for the first transaction")
            finally:
                release.set()
            first_result.result(timeout=10)
            return second_result.result(timeout=10)

    def change_settings(self, page_id, **data):
        return services.change_advanced_settings(
            Page.objects.get(pk=page_id), data=data, context=self.context,
        )

    def test_concurrent_reverse_id_is_revalidated_after_waiting(self):
        with self.assertRaises(ValidationError) as caught:
            self.overlap(
                lambda: self.change_settings(self.parent.pk, reverse_id="shared"),
                lambda: self.change_settings(self.other.pk, reverse_id="shared"),
            )
        self.assertIn("reverse_id", caught.exception.message_dict)
        self.assertEqual(Page.objects.filter(reverse_id="shared").count(), 1)

    def test_api_creation_waits_for_namespace_claim(self):
        with self.assertRaises(ValidationError) as caught:
            self.overlap(
                lambda: self.change_settings(
                    self.parent.pk, application_urls="NamespacedApp", application_namespace="shared",
                ),
                lambda: create_page(
                    "New", "nav_playground.html", "en", site=self.site,
                    apphook="NamespacedApp", apphook_namespace="shared", context=self.context,
                ),
            )
        self.assertIn("application_namespace", caught.exception.message_dict)
        self.assertEqual(Page.objects.filter(application_namespace="shared").count(), 1)

    def test_concurrent_settings_edits_preserve_both_changes(self):
        self.overlap(
            lambda: self.change_settings(self.parent.pk, login_required=True),
            lambda: self.change_settings(self.parent.pk, reverse_id="changed"),
        )
        self.parent.refresh_from_db()
        self.assertTrue(self.parent.login_required)
        self.assertEqual(self.parent.reverse_id, "changed")

    def test_creation_uses_parent_path_committed_while_waiting(self):
        # Prime the same caches an admin form or an API adapter might have read.
        self.assertEqual(self.parent.get_path("en"), "parent")
        content_id = self.parent.get_admin_content("en").pk
        child = self.overlap(
            lambda: services.change_page_content(
                PageContent.admin_manager.get(pk=content_id), data={"slug": "renamed"}, context=self.context,
            ),
            lambda: services.add_page(
                site=self.site, parent_page=self.parent, source=None, language="en",
                content_data={"title": "Child", "slug": "child"}, context=self.context,
            ),
        )
        self.assertEqual(PageUrl.objects.get(page=child.page, language="en").path, "renamed/child")

    def test_creation_uses_parent_position_committed_by_move(self):
        child = self.overlap(
            lambda: services.move_page(
                Page.objects.get(pk=self.parent.pk), Page.objects.get(pk=self.other.pk),
                "last-child", context=self.context,
            ),
            lambda: create_page(
                "Child", "nav_playground.html", "en", parent=self.parent, context=self.context,
            ),
        )
        self.assertEqual(PageUrl.objects.get(page=child, language="en").path, "other/parent/child")
        child.refresh_from_db()
        self.parent.refresh_from_db()
        self.assertEqual(child.depth, self.parent.depth + 1)
        self.assertTrue(child.path.startswith(self.parent.path))

    def test_concurrent_url_creation_is_a_field_error(self):
        with self.assertRaises(ValidationError) as caught:
            self.overlap(
                lambda: create_page("Shared", "nav_playground.html", "en", site=self.site, context=self.context),
                lambda: services.add_page(
                    site=self.site, parent_page=None, source=None, language="en",
                    content_data={"title": "Shared", "slug": "shared"}, context=self.context,
                ),
            )
        self.assertIn("slug", caught.exception.message_dict)
        self.assertEqual(PageUrl.objects.filter(path="shared", language="en").count(), 1)

    def test_concurrent_translation_creation_is_a_field_error(self):
        with self.assertRaises(ValidationError) as caught:
            self.overlap(
                lambda: create_page_content("de", "Deutsch", self.parent, context=self.context),
                lambda: services.add_translation(
                    Page.objects.get(pk=self.parent.pk), language="de",
                    content_data={"title": "Deutsch"}, context=self.context,
                ),
            )
        self.assertIn("language", caught.exception.message_dict)
        self.assertEqual(PageContent.admin_manager.filter(page=self.parent, language="de").count(), 1)
