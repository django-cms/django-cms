"""
Tests for apphook URL reloading when creating language variants.

This tests the fix for issue #8357 where creating new language variants
for pages with apphooks causes NoReverseMatch exceptions.

The fix works by ensuring that when a new PageContent (language variant) is
created for a page with an apphook, the set_restart_trigger() function is
called, which schedules a URL reload for the next request.

The test suite includes:
- Integration test that verifies UrlconfRevision actually changes via admin
- Unit tests that verify set_restart_trigger() is called at the right times
"""
from unittest.mock import patch

from django.test import override_settings

from cms.api import create_page, create_page_content
from cms.models import Page, UrlconfRevision
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import apphooks


@override_settings(
    MIDDLEWARE=['cms.middleware.utils.ApphookReloadMiddleware'] + [
        m for m in __import__('django.conf', fromlist=['settings']).settings.MIDDLEWARE  # noqa: E501
        if m != 'cms.middleware.utils.ApphookReloadMiddleware'
    ]
)
class ApphookReloadLanguageVariantTests(CMSTestCase):
    """Test URL reloading when creating language variants for apphook pages."""

    def test_new_language_variant_triggers_url_reload_via_admin(self):
        """
        Integration test: Creating a new language variant via the admin
        interface for a page with an apphook triggers URL reload and updates
        the UrlconfRevision.

        This is the end-to-end test that verifies the actual bug fix - that
        the URL revision changes when a new language variant is created,
        ensuring apphook URLs are available for the new language.
        """
        superuser = self.get_superuser()

        with apphooks(SampleApp):
            with self.login_user_context(superuser):
                # Create a page with an apphook in English
                page = create_page(
                    title="Test Page",
                    template="nav_playground.html",
                    language="en",
                    apphook="SampleApp",
                    apphook_namespace="test_app"
                )

                # Get the initial URL revision
                initial_revision, _ = UrlconfRevision.get_or_create_revision()

                # Create a new language variant via admin (simulating user action)
                endpoint = self.get_admin_url(Page, 'add')
                page_data = {
                    'title': 'Test Seite',
                    'slug': 'test-seite',
                    'language': 'de',
                    'template': 'nav_playground.html',
                    'page': page.pk,
                }

                # Make the HTTP request - this will trigger request_finished properly
                self.client.post(endpoint, page_data)

                # Check that the URL revision has changed
                new_revision, _ = UrlconfRevision.get_or_create_revision()
                self.assertNotEqual(
                    initial_revision,
                    new_revision,
                    "URL revision should change when creating a language variant "
                    "for an apphook page via admin interface"
                )

    @patch('cms.signals.pagecontent.set_restart_trigger')
    def test_new_language_variant_triggers_url_reload(self, mock_set_restart_trigger):
        """
        Unit test: Creating a new language variant for a page with an apphook
        calls set_restart_trigger().

        This verifies that the signal handler correctly identifies when a new
        language variant is created for an apphook page and schedules a URL reload.
        """
        with apphooks(SampleApp):
            # Create a page with an apphook in English
            page = create_page(
                title="Test Page",
                template="nav_playground.html",
                language="en",
                apphook="SampleApp",
                apphook_namespace="test_app"
            )

            # Reset the mock to ignore the call from page creation
            mock_set_restart_trigger.reset_mock()

            # Create a new language variant (German)
            # This should trigger URL reloading
            create_page_content(
                language="de",
                title="Test Seite",
                page=page
            )

            # Verify that set_restart_trigger was called
            mock_set_restart_trigger.assert_called_once()

    @patch('cms.signals.pagecontent.set_restart_trigger')
    def test_new_language_variant_without_apphook_no_reload(self, mock_set_restart_trigger):
        """
        Test that creating a new language variant for a page without an
        apphook does NOT trigger URL reloading.
        """
        # Create a page without an apphook in English
        page = create_page(
            title="Test Page",
            template="nav_playground.html",
            language="en"
        )

        # Reset the mock to ignore any previous calls
        mock_set_restart_trigger.reset_mock()

        # Create a new language variant (German)
        # This should NOT trigger URL reloading
        create_page_content(
            language="de",
            title="Test Seite",
            page=page
        )

        # Verify that set_restart_trigger was NOT called
        mock_set_restart_trigger.assert_not_called()

    @patch('cms.signals.pagecontent.set_restart_trigger')
    def test_signal_handler_called_for_apphook_page(self,
                                                    mock_set_restart_trigger):
        """
        Test that the signal handler is called when creating a language
        variant for a page with an apphook.
        """
        with apphooks(SampleApp):
            # Create a page with an apphook
            page = create_page(
                title="Test Page",
                template="nav_playground.html",
                language="en",
                apphook="SampleApp",
                apphook_namespace="test_app"
            )

            # Reset the mock to ignore the call from page creation
            mock_set_restart_trigger.reset_mock()

            # Create a new language variant
            create_page_content(
                language="de",
                title="Test Seite",
                page=page
            )

            # Verify that set_restart_trigger was called
            mock_set_restart_trigger.assert_called_once()

    @patch('cms.signals.pagecontent.set_restart_trigger')
    def test_signal_handler_not_called_for_non_apphook_page(
            self, mock_set_restart_trigger):
        """
        Test that the signal handler is NOT called when creating a language
        variant for a page without an apphook.
        """
        # Create a page without an apphook
        page = create_page(
            title="Test Page",
            template="nav_playground.html",
            language="en"
        )

        # Reset the mock to ignore any previous calls
        mock_set_restart_trigger.reset_mock()

        # Create a new language variant
        create_page_content(
            language="de",
            title="Test Seite",
            page=page
        )

        # Verify that set_restart_trigger was NOT called
        mock_set_restart_trigger.assert_not_called()

    @patch('cms.signals.pagecontent.set_restart_trigger')
    def test_signal_handler_not_called_for_existing_content_update(
            self, mock_set_restart_trigger):
        """
        Test that the signal handler is NOT called when updating existing
        PageContent (only when creating new ones).
        """
        with apphooks(SampleApp):
            # Create a page with an apphook
            page = create_page(
                title="Test Page",
                template="nav_playground.html",
                language="en",
                apphook="SampleApp",
                apphook_namespace="test_app"
            )

            # Reset the mock to ignore the call from page creation
            mock_set_restart_trigger.reset_mock()

            # Update the existing page content (not creating new)
            page_content = page.get_content_obj("en")
            page_content.title = "Updated Title"
            page_content.save()

            # Verify that set_restart_trigger was NOT called for updates
            mock_set_restart_trigger.assert_not_called()
