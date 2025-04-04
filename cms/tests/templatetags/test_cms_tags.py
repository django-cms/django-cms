import os
import django
import unittest
from django.template import Context, Template
from django.test import TestCase
from django.urls import NoReverseMatch

# Ensure settings are loaded before tests run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.settings")
django.setup()

class TestCmsTags(TestCase):
    """Test cases for the cms_tags.py template tags."""

    def test_page_url_tag_non_existing_page(self):
        """Test page_url tag with a non-existing page (should return empty string)."""
        template = Template("{% load cms_tags %}{% page_url 'non-existent' as url %}{{ url }}")
        context = Context({})
        rendered = template.render(context)

        # Print output for debugging
        print("\nTest: Non-Existing Page URL")
        print(f"Rendered Output: '{rendered.strip()}'")

        self.assertEqual(rendered.strip(), "")

    def test_page_url_tag_handles_noreversematch(self):
        """Test that the page_url tag does not crash with NoReverseMatch."""
        template = Template("{% load cms_tags %}{% page_url 'invalid-page' as url %}{{ url }}")
        context = Context({})

        try:
            rendered = template.render(context)
            print("\nTest: Handles NoReverseMatch")
            print(f"Rendered Output: '{rendered.strip()}'")
        except NoReverseMatch:
            self.fail("NoReverseMatch should not be raised.")

        self.assertEqual(rendered.strip(), "")