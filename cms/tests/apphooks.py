# -*- coding: utf-8 -*-
from __future__ import with_statement
import sys

from django.core.urlresolvers import clear_url_caches, reverse
from django.utils import six

from cms.api import create_page, create_title
from cms.apphook_pool import apphook_pool
from cms.appresolver import applications_page_check, clear_app_resolvers, get_app_patterns
from cms.models import Title
from cms.test_utils.testcases import CMSTestCase, SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.tests.menu_utils import DumbPageLanguageUrl
from cms.utils.compat.dj import get_user_model
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import force_language


APP_NAME = 'SampleApp'
NS_APP_NAME = 'NamespacedApp'
APP_MODULE = "cms.test_utils.project.sampleapp.cms_app"


class ApphooksTestCase(CMSTestCase):
    def setUp(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]

        self.reload_urls()
        apphook_pool.clear()

    def tearDown(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]

        self.reload_urls()
        apphook_pool.clear()

    def reload_urls(self):
        from django.conf import settings

        url_modules = [
            'cms.urls',
            # TODO: Add here intermediary modules which may
            #       include() the 'cms.urls' if it isn't included
            #       directly in the root urlconf.
            # '...',
            'cms.test_utils.project.second_cms_urls_for_apphook_tests',
            'cms.test_utils.project.urls_for_apphook_tests',
            settings.ROOT_URLCONF,
        ]

        clear_app_resolvers()
        clear_url_caches()

        for module in url_modules:
            if module in sys.modules:
                del sys.modules[module]

    def create_base_structure(self, apphook, title_langs, namespace=None):
        apphook_pool.clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        self.superuser = superuser
        page = create_page("home", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        create_title('de', page.get_title(), page)
        page.publish('de')
        child_page = create_page("child_page", "nav_playground.html", "en",
                                 created_by=superuser, published=True, parent=page)
        create_title('de', child_page.get_title(), child_page)
        child_page.publish('de')
        child_child_page = create_page("child_child_page", "nav_playground.html",
                                       "en", created_by=superuser, published=True, parent=child_page, apphook=apphook,
                                       apphook_namespace=namespace)
        create_title("de", child_child_page.get_title(), child_child_page)
        child_child_page.publish('de')
        # publisher_public is set to draft on publish, issue with onetoone reverse
        child_child_page = self.reload(child_child_page)

        if isinstance(title_langs, six.string_types):
            titles = child_child_page.publisher_public.get_title_obj(title_langs)
        else:
            titles = [child_child_page.publisher_public.get_title_obj(l) for l in title_langs]

        self.reload_urls()

        return titles

    def test_explicit_apphooks(self):
        """
        Test explicit apphook loading with the CMS_APPHOOKS setting.
        """
        apphooks = (
            '%s.%s' % (APP_MODULE, APP_NAME),
        )
        with SettingsOverride(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(app_names, [APP_NAME])
            apphook_pool.clear()

    def test_implicit_apphooks(self):
        """
        Test implicit apphook loading with INSTALLED_APPS cms_app.py
        """

        apps = ['cms.test_utils.project.sampleapp']
        with SettingsOverride(INSTALLED_APPS=apps, ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests'):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 4)
            self.assertIn(NS_APP_NAME, app_names)
            self.assertIn(APP_NAME, app_names)
            apphook_pool.clear()

    def test_apphook_on_root(self):

        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests'):
            apphook_pool.clear()
            superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
            page = create_page("apphooked-page", "nav_playground.html", "en",
                               created_by=superuser, published=True, apphook="SampleApp")
            blank_page = create_page("not-apphooked-page", "nav_playground.html", "en",
                                     created_by=superuser, published=True, apphook="", slug='blankapp')
            english_title = page.title_set.all()[0]
            self.assertEqual(english_title.language, 'en')
            create_title("de", "aphooked-page-de", page)
            self.assertTrue(page.publish('en'))
            self.assertTrue(page.publish('de'))
            self.assertTrue(blank_page.publish('en'))
            with force_language("en"):
                response = self.client.get(self.get_pages_root())
            self.assertTemplateUsed(response, 'sampleapp/home.html')
            self.assertContains(response, '<--noplaceholder-->')
            response = self.client.get('/en/blankapp/')
            self.assertTemplateUsed(response, 'nav_playground.html')

            apphook_pool.clear()

    def test_apphook_on_root_reverse(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests'):
            apphook_pool.clear()
            superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
            page = create_page("apphooked-page", "nav_playground.html", "en",
                               created_by=superuser, published=True, apphook="SampleApp")
            create_title("de", "aphooked-page-de", page)
            self.assertTrue(page.publish('de'))
            self.assertTrue(page.publish('en'))

            self.reload_urls()

            self.assertFalse(reverse('sample-settings').startswith('//'))

            apphook_pool.clear()

    def test_get_page_for_apphook(self):

        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title, de_title = self.create_base_structure(APP_NAME, ['en', 'de'])
            with force_language("en"):
                path = reverse('sample-settings')
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'

            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, en_title.page.pk)

            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)

            self.assertTemplateUsed(response, 'sampleapp/home.html')
            self.assertContains(response, en_title.title)
            with force_language("de"):
                path = reverse('sample-settings')
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'de'
            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash and language prefix
            self.assertEqual(attached_to_page.pk, de_title.page.pk)

            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/home.html')
            self.assertContains(response, de_title.title)

            apphook_pool.clear()

    def test_apphook_permissions(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title, de_title = self.create_base_structure(APP_NAME, ['en', 'de'])

            with force_language("en"):
                path = reverse('sample-settings')

            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)

            page = en_title.page.publisher_public
            page.login_required = True
            page.save()
            page.publish('en')

            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            apphook_pool.clear()

    def test_apphooks_with_excluded_permissions(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title = self.create_base_structure('SampleAppWithExcludedPermissions', 'en')

            with force_language("en"):
                excluded_path = reverse('excluded:example')
                not_excluded_path = reverse('not_excluded:example')

            page = en_title.page.publisher_public
            page.login_required = True
            page.save()
            page.publish('en')

            excluded_response = self.client.get(excluded_path)
            not_excluded_response = self.client.get(not_excluded_path)
            self.assertEqual(excluded_response.status_code, 200)
            self.assertEqual(not_excluded_response.status_code, 302)

            apphook_pool.clear()

    def test_get_page_for_apphook_on_preview_or_edit(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.urls_3'):
            if get_user_model().USERNAME_FIELD == 'email':
                superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin@admin.com')
            else:
                superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')

            page = create_page("home", "nav_playground.html", "en",
                               created_by=superuser, published=True, apphook=APP_NAME)
            create_title('de', page.get_title(), page)
            page.publish('en')
            page.publish('de')
            page.save()
            public_page = page.get_public_object()

            with self.login_user_context(superuser):
                with force_language("en"):
                    path = reverse('sample-settings')
                    request = self.get_request(path + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                    request.LANGUAGE_CODE = 'en'
                    attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
                    response = self.client.get(path+"?edit")
                    self.assertContains(response, '?redirect=')
                with force_language("de"):
                    path = reverse('sample-settings')
                    request = self.get_request(path + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                    request.LANGUAGE_CODE = 'de'
                    attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
                    self.assertEqual(attached_to_page.pk, public_page.pk)

    def test_get_root_page_for_apphook_with_instance_namespace(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title = self.create_base_structure(NS_APP_NAME, 'en', 'instance_ns')

            self.reload_urls()
            with force_language("en"):
                reverse("example_app:example")
                reverse("example1:example")
                reverse("example2:example")
                path = reverse('namespaced_app_ns:sample-root')
                path_instance = reverse('instance_ns:sample-root')
            self.assertEqual(path, path_instance)

            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'

            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, en_title.page.pk)

            apphook_pool.clear()

    def test_get_child_page_for_apphook_with_instance_namespace(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title = self.create_base_structure(NS_APP_NAME, 'en', 'instance_ns')
            with force_language("en"):
                path = reverse('namespaced_app_ns:sample-settings')
                path_instance1 = reverse('instance_ns:sample-settings')
                path_instance2 = reverse('namespaced_app_ns:sample-settings', current_app='instance_ns')
            self.assertEqual(path, path_instance1)
            self.assertEqual(path, path_instance2)

            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'
            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, en_title.page_id)
            apphook_pool.clear()

    def test_get_sub_page_for_apphook_with_implicit_current_app(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title = self.create_base_structure(NS_APP_NAME, 'en', 'namespaced_app_ns')
            with force_language("en"):
                path = reverse('namespaced_app_ns:current-app')
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'

            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, en_title.page.pk)

            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/app.html')
            self.assertContains(response, 'namespaced_app_ns')
            self.assertContains(response, path)

            apphook_pool.clear()

    def test_get_i18n_apphook_with_explicit_current_app(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            titles = self.create_base_structure(NS_APP_NAME, ['en', 'de'], 'instance_1')
            public_de_title = titles[1]
            de_title = Title.objects.get(page=public_de_title.page.publisher_draft, language="de")
            de_title.slug = "de"
            de_title.save()
            de_title.page.publish('de')

            page2 = create_page("page2", "nav_playground.html",
                                "en", created_by=self.superuser, published=True, parent=de_title.page.parent,
                                apphook=NS_APP_NAME,
                                apphook_namespace="instance_2")
            create_title("de", "de_title", page2, slug="slug")
            page2.publish('de')
            clear_app_resolvers()
            clear_url_caches()

            if APP_MODULE in sys.modules:
                del sys.modules[APP_MODULE]

            self.reload_urls()
            with force_language("de"):
                reverse('namespaced_app_ns:current-app', current_app="instance_1")
                reverse('namespaced_app_ns:current-app', current_app="instance_2")
                reverse('namespaced_app_ns:current-app')
            with force_language("en"):
                reverse('namespaced_app_ns:current-app', current_app="instance_1")
                reverse('namespaced_app_ns:current-app', current_app="instance_2")
                reverse('namespaced_app_ns:current-app')




    def test_apphook_include_extra_parameters(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            self.create_base_structure(NS_APP_NAME, ['en', 'de'], 'instance_1')
            with force_language("en"):
                path = reverse('namespaced_app_ns:extra_second')
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/extra.html')
            self.assertContains(response, 'someopts')

    def test_get_sub_page_for_apphook_with_explicit_current_app(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            en_title = self.create_base_structure(NS_APP_NAME, 'en', 'instance_ns')
            with force_language("en"):
                path = reverse('namespaced_app_ns:current-app')

            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'

            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, en_title.page.pk)

            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/app.html')
            self.assertContains(response, 'instance_ns')
            self.assertContains(response, path)

            apphook_pool.clear()

    def test_include_urlconf(self):
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests'):
            self.create_base_structure(APP_NAME, 'en')

            path = reverse('extra_second')
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/extra.html')
            self.assertContains(response, "test included urlconf")

            path = reverse('extra_first')
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/extra.html')
            self.assertContains(response, "test urlconf")
            with force_language("de"):
                path = reverse('extra_first')
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/extra.html')
            self.assertContains(response, "test urlconf")
            with force_language("de"):
                path = reverse('extra_second')
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/extra.html')
            self.assertContains(response, "test included urlconf")

            apphook_pool.clear()

    def test_apphook_breaking_under_home_with_new_path_caching(self):
        with SettingsOverride(CMS_PERMISSION=False, ROOT_URLCONF='cms.test_utils.project.urls_2'):
            home = create_page("home", "nav_playground.html", "en", published=True)
            child = create_page("child", "nav_playground.html", "en", published=True, parent=home)
            # not-home is what breaks stuff, because it contains the slug of the home page
            not_home = create_page("not-home", "nav_playground.html", "en", published=True, parent=child)
            create_page("subchild", "nav_playground.html", "en", published=True, parent=not_home, apphook='SampleApp')
            with force_language("en"):
                self.reload_urls()
                urlpatterns = get_app_patterns()
                resolver = urlpatterns[0]
                url = resolver.reverse('sample-root')
                self.assertEqual(url, 'child/not-home/subchild/')

    def test_apphook_urlpattern_order(self):
        # this one includes the actual cms.urls, so it can be tested if
        # they are loaded in the correct order (the cms page pattern must be last)
        # (the other testcases replicate the inclusion code and thus don't test this)
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.urls'):
            self.create_base_structure(APP_NAME, 'en')
            path = reverse('extra_second')
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/extra.html')
            self.assertContains(response, "test included urlconf")

    def test_apphooks_receive_url_params(self):
        # make sure that urlparams actually reach the apphook views
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.urls'):
            self.create_base_structure(APP_NAME, 'en')
            path = reverse('sample-params', kwargs=dict(my_params='is-my-param-really-in-the-context-QUESTIONMARK'))
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/home.html')
            self.assertContains(response, 'my_params: is-my-param-really-in-the-context-QUESTIONMARK')

    def test_multiple_apphooks(self):
        # test for #1538
        with SettingsOverride(ROOT_URLCONF='cms.test_utils.project.third_urls_for_apphook_tests'):
            apphook_pool.clear()
            superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
            create_page("home", "nav_playground.html", "en", created_by=superuser, published=True, )
            create_page("apphook1-page", "nav_playground.html", "en",
                        created_by=superuser, published=True, apphook="SampleApp")
            create_page("apphook2-page", "nav_playground.html", "en",
                        created_by=superuser, published=True, apphook="SampleApp2")

            reverse('sample-root')
            reverse('sample2-root')

            apphook_pool.clear()


class ApphooksPageLanguageUrlTestCase(SettingsOverrideTestCase):
    settings_overrides = {'ROOT_URLCONF': 'cms.test_utils.project.second_urls_for_apphook_tests'}

    def setUp(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        self.reload_urls()

    def tearDown(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        apphook_pool.clear()

    def reload_urls(self):
        from django.conf import settings

        url_modules = [
            'cms.urls',
            'cms.test_utils.project.second_cms_urls_for_apphook_tests',
            settings.ROOT_URLCONF,
        ]

        clear_app_resolvers()
        clear_url_caches()

        for module in url_modules:
            if module in sys.modules:
                del sys.modules[module]

    def test_page_language_url_for_apphook(self):

        apphook_pool.clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = create_page("home", "nav_playground.html", "en",
                           created_by=superuser)
        create_title('de', page.get_title(), page)
        page.publish('en')
        page.publish('de')

        child_page = create_page("child_page", "nav_playground.html", "en",
                                 created_by=superuser, parent=page)
        create_title('de', child_page.get_title(), child_page)
        child_page.publish('en')
        child_page.publish('de')

        child_child_page = create_page("child_child_page", "nav_playground.html",
                                       "en", created_by=superuser, parent=child_page, apphook='SampleApp')
        create_title("de", '%s_de' % child_child_page.get_title(), child_child_page)
        child_child_page.publish('en')
        child_child_page.publish('de')

        # publisher_public is set to draft on publish, issue with one to one reverse
        child_child_page = self.reload(child_child_page)
        with force_language("en"):
            path = reverse('extra_first')

        request = self.get_request(path)
        request.LANGUAGE_CODE = 'en'
        request.current_page = child_child_page

        fake_context = {'request': request}
        tag = DumbPageLanguageUrl()

        output = tag.get_context(fake_context, 'en')
        url = output['content']

        self.assertEqual(url, '/en/child_page/child_child_page/extra_1/')

        output = tag.get_context(fake_context, 'de')
        url = output['content']
        # look the extra "_de"
        self.assertEqual(url, '/de/child_page/child_child_page_de/extra_1/')

        output = tag.get_context(fake_context, 'fr')
        url = output['content']
        self.assertEqual(url, '/fr/child_page/child_child_page/extra_1/')

        apphook_pool.clear()
