from __future__ import with_statement
from cms.apphook_pool import apphook_pool
from cms.test.testcases import SettingsOverrideTestCase
from cms.test.util.context_managers import SettingsOverride
from cms.views import _handle_no_page, details
from django.conf import settings
from django.core.urlresolvers import clear_url_caches
from django.http import Http404
import sys


APP_NAME = 'SampleApp'
APP_MODULE = "testapp.sampleapp.cms_app"


class ViewTests(SettingsOverrideTestCase):
    urls = 'testapp.urls_for_apphook_tests'
    settings_overrides = {'CMS_MODERATOR': False}
    
    def setUp(self):
        clear_url_caches()
    
    def test_01_handle_no_page(self):
        """
        Test handle nopage correctly works with DEBUG=True
        """
        request = self.get_request('/')
        slug = ''
        self.assertRaises(Http404, _handle_no_page, request, slug)
        with SettingsOverride(DEBUG=True):
            request = self.get_request('/')
            slug = ''
            response = _handle_no_page(request, slug)
            self.assertEqual(response.status_code, 200)
            
    def test_02_language_fallback(self):
        """
        Test language fallbacks in details view
        """
        self.create_page(published=True, language='en')
        request = self.get_request('/', 'de')
        response = details(request, '')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')
        with SettingsOverride(CMS_LANGUAGE_FALLBACK=False):
            self.assertRaises(Http404, details, request, '')
    
    def test_03_apphook_not_hooked(self):
        """
        Test details view when apphook pool has apphooks, but they're not
        actually hooked
        """
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        apphooks = (
            '%s.%s' % (APP_MODULE, APP_NAME),
        )
        self.create_page(published=True, language='en')
        with SettingsOverride(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            apphook_pool.clear()
    
    def test_04_redirect(self):
        redirect_one = 'https://www.django-cms.org/'
        redirect_two = '/'
        redirect_three = '/en/'
        # test external redirect
        one = self.create_page(
            published=True,
            language='en',
            title_extra={'redirect': redirect_one}
        )
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_one)
        
        # test internal language neutral redirect
        two = self.create_page(
            parent_page=one,
            published=True,
            language='en',
            title_extra={'redirect': redirect_two}
        )
        url = two.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')
        
        # test internal forced language redirect
        three = self.create_page(
            parent_page=one,
            published=True,
            language='en',
            title_extra={'redirect': redirect_three}
        )
        url = three.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_three)
    
    def test_05_redirect_to_page(self):
        one = self.create_page(
            published=True,
            language='en'
        )
        two = self.create_page(
            parent_page=one,
            published=True,
            language='en'
        )
        three = self.create_page(
            parent_page=one,
            published=True,
            language='en',
            title_extra={'redirect_to_page': two}
        )
        url = three.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], two.get_absolute_url())
    
    def test_06_login_required(self):
        self.create_page(
            published=True,
            language='en',
            login_required=True,
        )
        request = self.get_request('/')
        response = details(request, '')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '%s?next=/en/' % settings.LOGIN_URL)
        with SettingsOverride(i18n_installed=False):
            request = self.get_request('/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '%s?next=/' % settings.LOGIN_URL)