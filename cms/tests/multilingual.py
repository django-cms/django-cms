# -*- coding: utf-8 -*-
from cms.api import create_page, create_title, publish_page, add_plugin
from cms.middleware.multilingual import patch_response
from cms.test_utils.testcases import CMSTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import urllib


class MultilingualTestCase(CMSTestCase):
    def test_multilingual_url_middleware(self):
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
        
    def test_multilingual_page(self):
        page = create_page("mlpage", "nav_playground.html", "en")
        create_title("de", page.get_title(), page, slug=page.get_slug())
        page.rescan_placeholders()
        page = self.reload(page)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", 'de', body="test")
        add_plugin(placeholder, "TextPlugin", 'en', body="test")
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)
        user = User.objects.create_superuser('super', 'super@django-cms.org', 'super')
        page = publish_page(page, user, True)
        public = page.publisher_public
        placeholder = public.placeholders.all()[0]
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)

    def test_multiple_reverse_monkeypatch(self):
        """
        This test is not very well behaved, every following
        test that uses reverse will fail with a RuntimeException.
        """
        from cms.models import monkeypatch_reverse
        monkeypatch_reverse()
        monkeypatch_reverse()
        try:
            reverse('pages-root')
        except RuntimeError:
            self.fail('maximum recursion depth exceeded')
