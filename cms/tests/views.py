from __future__ import with_statement
import re

from cms.api import create_page, create_title
from cms.apphook_pool import apphook_pool
from cms.models import PagePermission
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.views import _handle_no_page, details
from cms.utils.i18n import force_language

from django.contrib.auth.models import Permission
from django.conf import settings
from django.core.urlresolvers import clear_url_caches
from django.http import Http404, HttpResponse
import sys


APP_NAME = 'SampleApp'
APP_MODULE = "cms.test_utils.project.sampleapp.cms_app"


class ViewTests(SettingsOverrideTestCase):
    urls = 'cms.test_utils.project.urls'

    settings_overrides = {'CMS_PERMISSION': True}

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
            request = self.get_request('/en/')
            slug = ''
            response = _handle_no_page(request, slug)
            self.assertEqual(response.status_code, 200)

    def test_incorrect_slug_for_language(self):
        """
        Test details view when page slug and current language don't match.
        In this case we refer to the user's current language and the page slug we have for that language.
        """
        create_page("home", "nav_playground.html", "en", published=True)
        cms_page = create_page("stevejobs", "nav_playground.html", "en", published=True)
        create_title("de", "jobs", cms_page)
        cms_page.publish()
        with force_language("de"):
            response = self.client.get('/de/stevejobs/')
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/de/jobs/')

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
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)
            apphook_pool.clear()
    
    def test_external_redirect(self):
        # test external redirect
        redirect_one = 'https://www.django-cms.org/'
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect=redirect_one)
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request,one.get_path("en"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_one)
        
    def test_internal_neutral_redirect(self):
        # test internal language neutral redirect
        redirect_one = 'https://www.django-cms.org/'
        redirect_two = '/'
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect=redirect_one)
        two = create_page("two", "nav_playground.html", "en", parent=one,
                          published=True, redirect=redirect_two)
        url = two.get_absolute_url()
        request = self.get_request(url)
        response = details(request, two.get_path())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')
        
    def test_internal_forced_redirect(self):
        # test internal forced language redirect
        redirect_one = 'https://www.django-cms.org/'
        redirect_three = '/en/'
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect=redirect_one)
        three = create_page("three", "nav_playground.html", "en", parent=one,
                            published=True, redirect=redirect_three)
        url = three.get_slug()
        request = self.get_request(url)
        response = details(request, url.strip('/'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_three)
        
    def test_redirect_to_self(self):
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect='/')
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, one.get_path())
        self.assertEqual(response.status_code, 200)
        
    def test_redirect_to_self_with_host(self):
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect='http://testserver/en/')
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, one.get_path())
        self.assertEqual(response.status_code, 200)
    
    def test_login_required(self):
        create_page("page", "nav_playground.html", "en", published=True,
                         login_required=True)
        plain_url = '/accounts/'
        login_rx = re.compile("%s\?(signin=|next=/en/)&" % plain_url)
        with SettingsOverride(LOGIN_URL=plain_url+'?signin'):
            request = self.get_request('/en/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))
        login_rx = re.compile("%s\?(signin=|next=/)&" % plain_url)
        with SettingsOverride(USE_I18N=False, LOGIN_URL='/accounts/?signin'):
            request = self.get_request('/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))

    def test_edit_permission(self):
        page = create_page("page", "nav_playground.html", "en", published=True)

        # Anon user
        response = self.client.get("/en/?edit")
        self.assertContains(response, "'edit_mode': false,", 1, 200)

        # Superuser
        user = self.get_superuser()
        self.client.login(username=user.username, password=user.username)
        response = self.client.get("/en/?edit")
        self.assertContains(response, "'edit_mode': true,", 1, 200)

        # Admin but with no permission
        user = self.get_staff_user_with_no_permissions()
        user.user_permissions.add(Permission.objects.get(codename='change_page'))

        self.client.login(username=user.username, password=user.username)
        response = self.client.get("/en/?edit")
        self.assertContains(response, "'edit_mode': false,", 1, 200)

        PagePermission.objects.create(can_change=True, user=user, page=page)
        response = self.client.get("/en/?edit")
        self.assertContains(response, "'edit_mode': true,", 1, 200)
