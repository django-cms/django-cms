# -*- coding: utf-8 -*-
from cms.middleware.multilingual import patch_response
from cms.test.testcases import CMSTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import urllib


class MultilingualTestCase(CMSTestCase):
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
        
    def test_02_multilingual_page(self):
        page = self.create_page()
        self.create_title(
            page=page,
            title=page.get_title(),
            slug=page.get_slug(),
            language='de'
        )
        page.rescan_placeholders()
        page = self.reload(page)
        placeholder = page.placeholders.all()[0]
        self.add_plugin(placeholder=placeholder, language='de')
        self.add_plugin(placeholder=placeholder, language='en')
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)
        user = User.objects.create_superuser('super', 'super@django-cms.org', 'super')
        page = self.publish_page(page, approve=True, user=user)
        public = page.publisher_public
        placeholder = public.placeholders.all()[0]
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)
