from __future__ import with_statement
from cms.api import create_page
from cms.apphook_pool import apphook_pool
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.views import _handle_no_page, details
from django.conf import settings
from django.core.urlresolvers import clear_url_caches
from django.http import Http404
import sys


APP_NAME = 'SampleApp'
APP_MODULE = "project.sampleapp.cms_app"


class ViewTests(SettingsOverrideTestCase):
    urls = 'project.urls_for_apphook_tests'
    settings_overrides = {'CMS_MODERATOR': False}
    
    def setUp(self):
        clear_url_caches()
    
    def test_handle_no_page(self):
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
            
    def test_language_fallback(self):
        """
        Test language fallbacks in details view
        """
        create_page("page", "nav_playground.html", "en", published=True)
        request = self.get_request('/', 'de')
        response = details(request, '')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')
        with SettingsOverride(CMS_LANGUAGE_FALLBACK=False):
            self.assertRaises(Http404, details, request, '')
    
    def test_apphook_not_hooked(self):
        """
        Test details view when apphook pool has apphooks, but they're not
        actually hooked
        """
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        apphooks = (
            '%s.%s' % (APP_MODULE, APP_NAME),
        )
        create_page("page2", "nav_playground.html", "en", published=True)
        with SettingsOverride(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            apphook_pool.clear()
    
    def test_redirect(self):
        redirect_one = 'https://www.django-cms.org/'
        redirect_two = '/'
        redirect_three = '/en/'
        # test external redirect
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect=redirect_one)
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_one)
        
        # test internal language neutral redirect
        two = create_page("two", "nav_playground.html", "en", parent=one,
                          published=True, redirect=redirect_two)
        url = two.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')
        
        # test internal forced language redirect
        three = create_page("three", "nav_playground.html", "en", parent=one,
                            published=True, redirect=redirect_three)
        url = three.get_absolute_url()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_three)
    
    def test_login_required(self):
        create_page("page", "nav_playground.html", "en", published=True,
                         login_required=True)
        request = self.get_request('/')
        response = details(request, '')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '%s?next=/en/' % settings.LOGIN_URL)
        with SettingsOverride(i18n_installed=False):
            request = self.get_request('/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '%s?next=/' % settings.LOGIN_URL)
