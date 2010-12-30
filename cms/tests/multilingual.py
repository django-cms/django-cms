from cms.middleware.multilingual import patch_response
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
import urllib


class MultilingualTestCase(TestCase):
    def test_01_multilingual_url_middleware(self):
        """
        Test the Multilingual URL Middleware correctly handles the various ways
        one can write URLs in HTML.
        """
        # stuff we need
        pages_root = urllib.unquote(reverse('pages-root'))
        language = "en"
        # single quoted a tag
        content = "<a href='/url/'>"
        output = patch_response(content, pages_root, language)
        expected = "<a href='/en/url/'>"
        self.assertEqual(output, expected)
        # double quoted a tag
        content = '<a href="/url/">'
        output = patch_response(content, pages_root, language)
        expected = '<a href="/en/url/">'
        self.assertEqual(output, expected)
        # single quoted a tag with a class and rel attribute
        content = "<a rel='rel' href='/url/' class='cms'>"
        output = patch_response(content, pages_root, language)
        expected = "<a rel='rel' href='/en/url/' class='cms'>"
        self.assertEqual(output, expected)
        # single quoted form tag
        content = "<form action='/url/'>"
        output = patch_response(content, pages_root, language)
        expected = "<form action='/en/url/'>"
        self.assertEqual(output, expected)
        # double quoted form tag
        content = '<form action="/url/">'
        output = patch_response(content, pages_root, language)
        expected = '<form action="/en/url/">'
        self.assertEqual(output, expected)