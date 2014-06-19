from __future__ import with_statement
import sys
from copy import copy

import re
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.urlresolvers import clear_url_caches
from django.http import Http404
from django.template import Variable
from cms.api import create_page
from cms.apphook_pool import apphook_pool
from cms.models import PagePermission
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.utils.compat import DJANGO_1_5
from cms.utils.conf import get_cms_setting
from cms.views import _handle_no_page, details
from menus.menu_pool import menu_pool


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
        response = details(request, one.get_path("en"))
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

    def test_redirect_with_toolbar(self):
        create_page("one", "nav_playground.html", "en", published=True,
                    redirect='/en/page2')
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            self.assertEqual(response.status_code, 200)

    def test_login_required(self):
        create_page("page", "nav_playground.html", "en", published=True,
                    login_required=True)
        plain_url = '/accounts/'
        login_rx = re.compile("%s\?(signin=|next=/en/)&" % plain_url)
        with SettingsOverride(LOGIN_URL=plain_url + '?signin'):
            request = self.get_request('/en/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))
        login_rx = re.compile("%s\?(signin=|next=/)&" % plain_url)
        with SettingsOverride(USE_I18N=False, LOGIN_URL=plain_url + '?signin'):
            request = self.get_request('/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))

    def test_edit_permission(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        # Anon user
        response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertNotContains(response, "cms_toolbar-item_switch", 200)

        # Superuser
        user = self.get_superuser()
        with self.login_user_context(user):
            response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertContains(response, "cms_toolbar-item_switch", 4, 200)

        # Admin but with no permission
        user = self.get_staff_user_with_no_permissions()
        user.user_permissions.add(Permission.objects.get(codename='change_page'))

        with self.login_user_context(user):
            response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertNotContains(response, "cms_toolbar-item_switch", 200)

        PagePermission.objects.create(can_change=True, user=user, page=page)
        with self.login_user_context(user):
            response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertContains(response, "cms_toolbar-item_switch", 4, 200)


class ContextTests(SettingsOverrideTestCase):
    urls = 'cms.test_utils.project.urls'

    def test_context_current_page(self):
        """
        Asserts the number of queries triggered by
        `cms.context_processors.cms_settings` and `cms.middleware.page`
        """
        from django.template import context

        page_template = "nav_playground.html"
        original_context = settings.TEMPLATE_CONTEXT_PROCESSORS
        new_context = copy(original_context)
        new_context.remove("cms.context_processors.cms_settings")
        page = create_page("page", page_template, "en", published=True)
        page_2 = create_page("page-2", page_template, "en", published=True,
                             parent=page)

        # Tests for standard django applications
        # 1 query is executed in get_app_patterns(), not related
        # to cms.context_processors.cms_settings.
        # Executing this oputside queries assertion context ensure
        # repetability
        self.client.get("/en/plain_view/")

        cache.clear()
        menu_pool.clear()
        context._standard_context_processors = None
        # Number of queries when context processors is not enabled
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=new_context):
            with self.assertNumQueries(FuzzyInt(0, 12)) as context:
                response = self.client.get("/en/plain_view/")
                if DJANGO_1_5:
                    num_queries = len(context.connection.queries) - context.starting_queries
                else:
                    num_queries = len(context.captured_queries)
                self.assertFalse('CMS_TEMPLATE' in response.context)
        cache.clear()
        menu_pool.clear()
        # Number of queries when context processor is enabled
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=original_context):
            # no extra query is run when accessing urls managed by standard
            # django applications
            with self.assertNumQueries(FuzzyInt(0, num_queries)):
                response = self.client.get("/en/plain_view/")
            # One query when determining current page
            with self.assertNumQueries(FuzzyInt(0, 1)):
                self.assertFalse(response.context['request'].current_page)
                self.assertFalse(response.context['request']._current_page_cache)
            # Zero more queries when determining the current template
            with self.assertNumQueries(0):
                # Template is the first in the CMS_TEMPLATES list
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, get_cms_setting('TEMPLATES')[0][0])
        cache.clear()
        menu_pool.clear()

        # Number of queries when context processors is not enabled
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=new_context):
            # Baseline number of queries
            with self.assertNumQueries(FuzzyInt(13, 17)) as context:
                response = self.client.get("/en/page-2/")
                if DJANGO_1_5:
                    num_queries_page = len(context.connection.queries) - context.starting_queries
                else:
                    num_queries_page = len(context.captured_queries)
        cache.clear()
        menu_pool.clear()

        # Number of queries when context processors is enabled
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=original_context):
            # Exactly the same number of queries are executed with and without
            # the context_processor
            with self.assertNumQueries(num_queries_page):
                response = self.client.get("/en/page-2/")
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, page_template)
        cache.clear()
        menu_pool.clear()
        page_2.template = 'INHERIT'
        page_2.save()
        page_2.publish('en')
        with SettingsOverride(TEMPLATE_CONTEXT_PROCESSORS=original_context):
            # One query more triggered as page inherits template from ancestor
            with self.assertNumQueries(num_queries_page + 1):
                response = self.client.get("/en/page-2/")
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, page_template)
