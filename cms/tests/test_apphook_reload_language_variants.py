"""
Tests for apphook URL reloading when creating language variants.

This tests the fix for issue #8357 where creating new language variants
for pages with apphooks causes NoReverseMatch exceptions.
"""
from unittest.mock import patch

from django.test import override_settings

from cms.api import create_page, create_page_content
from cms.models import UrlconfRevision
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

    def test_new_language_variant_triggers_url_reload(self):
        """
        Test that creating a new language variant for a page with an apphook
        triggers URL reloading.
        """
        with apphooks(SampleApp):
            # Create a page with an apphook in English
            page = create_page(
                title="Test Page",
                template="nav_playground.html",
                language="en",
                application_urls="SampleApp",
                application_namespace="test_app"
            )

            # Get the initial URL revision
            initial_revision, _ = UrlconfRevision.get_or_create_revision()

            # Create a new language variant (German)
            # This should trigger URL reloading
            create_page_content(
                language="de",
                title="Test Seite",
                page=page
            )

            # Check that the URL revision has changed
            new_revision, _ = UrlconfRevision.get_or_create_revision()
            self.assertNotEqual(
                initial_revision,
                new_revision,
                "URL revision should change when creating a language variant "
                "for an apphook page"
            )

    def test_new_language_variant_without_apphook_no_reload(self):
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

        # Get the initial URL revision
        initial_revision, _ = UrlconfRevision.get_or_create_revision()

        # Create a new language variant (German)
        # This should NOT trigger URL reloading
        create_page_content(
            language="de",
            title="Test Seite",
            page=page
        )

        # Check that the URL revision has NOT changed
        new_revision, _ = UrlconfRevision.get_or_create_revision()
        self.assertEqual(
            initial_revision,
            new_revision,
            "URL revision should NOT change when creating a language variant "
            "for a non-apphook page"
        )

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
                application_urls="SampleApp",
                application_namespace="test_app"
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
                application_urls="SampleApp",
                application_namespace="test_app"
            )

            # Reset the mock to ignore the call from page creation
            mock_set_restart_trigger.reset_mock()

            # Update the existing page content (not creating new)
            page_content = page.get_content_obj("en")
            page_content.title = "Updated Title"
            page_content.save()

            # Verify that set_restart_trigger was NOT called for updates
            mock_set_restart_trigger.assert_not_called()
