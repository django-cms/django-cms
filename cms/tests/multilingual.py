# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page, create_title, publish_page, add_plugin
from cms.middleware.multilingual import patch_response
from cms.models import Title
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE_ADD, 
                                      URL_CMS_PAGE, URL_CMS_PAGE_CHANGE,
                                      URL_CMS_PAGE_CHANGE_LANGUAGE)
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.sites.models import Site
from django.conf import settings
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

    def test_no_unnecessary_language_cookie(self):
        client = Client() # we need a fresh client to ensure no cookies are set
        response = client.get('/en/')
        self.assertIn('django_language', response.cookies)
        self.assertIn('sessionid', response.cookies)
        response = client.get('/')
        self.assertNotIn('django_language', response.cookies)
        self.assertNotIn('sessionid', response.cookies)


    def test_create_page(self):
        """
        Test that a page can be created via the admin
        and that a new language can be created afterwards
        """

        site = Site.objects.get_current()
        # Change site for this session
        page_data = self.get_new_page_data()

        # Create a new page, default language
        page_data = self.get_new_page_data()
        page_data['site'] = site.pk
        page_data['title'] = 'changed title'
        TESTLANG = settings.CMS_SITE_LANGUAGES[site.pk][0]
        page_data['language'] = TESTLANG

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            title = Title.objects.get(slug=page_data['slug'])
            self.assertNotEqual(title, None)
            page = title.page
            page.published = True
            page.save()
            self.assertEqual(page.get_title(), page_data['title'])
            self.assertEqual(page.get_slug(), page_data['slug'])
            self.assertEqual(page.placeholders.all().count(), 2)
            
            # were public instances created?
            title = Title.objects.drafts().get(slug=page_data['slug'])
        
            # Test that it's the default language
            self.assertEqual(title.language, TESTLANG,
                             "not the same language as specified in settings.CMS_LANGUAGES")
            
            # Publish the old page version
            page_data['published'] = True
            response = self.client.post(URL_CMS_PAGE_CHANGE_LANGUAGE % (page.pk, TESTLANG),
                                        page_data)
            page = page.reload()
            
            # Create a different language using the edit admin page
            page_data2 = page_data.copy()
            page_data2['title'] = 'ein Titel'
            page_data2['slug'] = 'ein-slug'
            TESTLANG2 = 'de'
            page_data2['language'] = TESTLANG2
            
            # Ensure that the language version is not returned
            # since it does not exist
            self.assertRaises(Title.DoesNotExist,
                              page.get_title_obj,
                              language=TESTLANG2, fallback=False)
            
            # Now create it
            response = self.client.post(URL_CMS_PAGE_CHANGE_LANGUAGE % (page.pk, TESTLANG2),
                                        page_data2)
            
            page = page.reload()
            
            # Test the new language version
            self.assertEqual(page.get_title(language=TESTLANG2), page_data2['title'])
            self.assertEqual(page.get_slug(language=TESTLANG2), page_data2['slug'])
            
            # Test the default language version (TESTLANG)
            self.assertEqual(page.get_slug(language=TESTLANG, fallback=False), page_data['slug'])
            self.assertEqual(page.get_title(language=TESTLANG, fallback=False), page_data['title'])
            self.assertEqual(page.get_slug(fallback=False), page_data['slug'])
            self.assertEqual(page.get_title(fallback=False), page_data['title'])
            