import sys

import mock
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import checks
from django.core.cache import cache
from django.core.checks.urls import check_url_config
from django.test.utils import override_settings
from django.urls import NoReverseMatch, clear_url_caches, resolve, reverse
from django.utils.timezone import now
from django.utils.translation import override as force_language

from cms.admin.forms import AdvancedSettingsForm
from cms.api import create_page, create_title
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.appresolver import (
    applications_page_check, clear_app_resolvers, get_app_patterns,
)
from cms.constants import PUBLISHER_STATE_DIRTY
from cms.middleware.page import get_page
from cms.models import Page, Title
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import CMSTestCase
from cms.tests.test_menu_utils import DumbPageLanguageUrl
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse
from menus.menu_pool import menu_pool
from menus.utils import DefaultLanguageChanger

APP_NAME = 'SampleApp'
NS_APP_NAME = 'NamespacedApp'
APP_MODULE = "cms.test_utils.project.sampleapp.cms_apps"
MENU_MODULE = "cms.test_utils.project.sampleapp.cms_menus"


class ApphooksTestCase(CMSTestCase):
    def setUp(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]

        self.reload_urls()
        self.apphook_clear()

    def tearDown(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]

        self.reload_urls()
        self.apphook_clear()

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
            APP_MODULE,
            settings.ROOT_URLCONF,
        ]

        clear_app_resolvers()
        clear_url_caches()

        for module in url_modules:
            if module in sys.modules:
                del sys.modules[module]

    def _fake_logentry(self, instance_id, user, text, model=Page):
        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(model).pk,
            object_id=instance_id,
            object_repr=text,
            action_flag=CHANGE,
        )
        entry = LogEntry.objects.filter(user=user, action_flag__in=(CHANGE,))[0]
        session = self.client.session
        session['cms_log_latest'] = entry.pk
        session.save()

    def create_base_structure(self, apphook, title_langs, namespace=None):
        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        self.superuser = superuser
        page = create_page(
            "home", "nav_playground.html", "en",
            created_by=superuser, published=True
        )
        create_title('de', page.get_title(), page)
        page.publish('de')
        child_page = create_page(
            "child_page", "nav_playground.html", "en",
            created_by=superuser, published=True, parent=page
        )
        create_title('de', child_page.get_title(), child_page)
        child_page.publish('de')
        child_child_page = create_page(
            "child_child_page", "nav_playground.html",
            "en", created_by=superuser, published=True, parent=child_page, apphook=apphook,
            apphook_namespace=namespace
        )
        create_title("de", child_child_page.get_title(), child_child_page)
        child_child_page.publish('de')
        # publisher_public is set to draft on publish, issue with onetoone reverse
        child_child_page = self.reload(child_child_page)

        if isinstance(title_langs, str):
            titles = child_child_page.publisher_public.get_title_obj(title_langs)
        else:
            titles = [child_child_page.publisher_public.get_title_obj(lang) for lang in title_langs]

        self.reload_urls()

        return titles

    @override_settings(ROOT_URLCONF='cms.test_utils.project.fourth_urls_for_apphook_tests')
    def test_check_url_config(self):
        """
        Test for urls config check.
        """
        self.apphook_clear()
        result = check_url_config(None)
        self.assertEqual(len(result), 0)

    @override_settings(CMS_APPHOOKS=['%s.%s' % (APP_MODULE, APP_NAME)])
    def test_explicit_apphooks(self):
        """
        Test explicit apphook loading with the CMS_APPHOOKS setting.
        """
        self.apphook_clear()
        hooks = apphook_pool.get_apphooks()
        app_names = [hook[0] for hook in hooks]
        self.assertEqual(len(hooks), 1)
        self.assertEqual(app_names, [APP_NAME])
        self.apphook_clear()

    @override_settings(
        INSTALLED_APPS=['cms.test_utils.project.sampleapp'],
        ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests',
    )
    def test_implicit_apphooks(self):
        """
        Test implicit apphook loading with INSTALLED_APPS cms_apps.py
        """
        self.apphook_clear()
        hooks = apphook_pool.get_apphooks()
        app_names = [hook[0] for hook in hooks]
        self.assertEqual(len(hooks), 8)
        self.assertIn(NS_APP_NAME, app_names)
        self.assertIn(APP_NAME, app_names)
        self.apphook_clear()

    def test_apphook_on_homepage(self):
        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = self.create_homepage("apphooked-page", "nav_playground.html", "en",
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

        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests')
    def test_apphook_does_not_crash_django_checks(self):
        # This test case reproduced the situation causing the error reported in issue #6717.
        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        create_page("apphooked-page", "nav_playground.html", "en",
                    created_by=superuser, published=True, apphook="SampleApp")
        self.reload_urls()
        checks.run_checks()
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests')
    def test_apphook_on_root_reverse(self):
        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = create_page("apphooked-page", "nav_playground.html", "en",
                           created_by=superuser, published=True, apphook="SampleApp")
        create_title("de", "aphooked-page-de", page)
        self.assertTrue(page.publish('de'))
        self.assertTrue(page.publish('en'))

        self.reload_urls()

        self.assertFalse(reverse('sample-settings').startswith('//'))
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests')
    def test_multisite_apphooks(self):
        self.apphook_clear()
        site1, _ = Site.objects.get_or_create(pk=1)
        site2, _ = Site.objects.get_or_create(pk=2)
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        home_site_1 = create_page(
            "home", "nav_playground.html", "en", created_by=superuser, published=True, site=site1
        )
        home_site_2 = create_page(
            "home", "nav_playground.html", "de", created_by=superuser, published=True, site=site2
        )

        page_a_1 = create_page(
            "apphooked-page", "nav_playground.html", "en", created_by=superuser, published=True, parent=home_site_1,
            apphook=NS_APP_NAME, apphook_namespace="instance"
        )
        page_a_2 = create_page(
            "apphooked-page", "nav_playground.html", "de", created_by=superuser, published=True, parent=home_site_1,
        )
        page_b_1 = create_page(
            "apphooked-page", "nav_playground.html", "de", created_by=superuser, published=True, parent=home_site_2,
            site=site2
        )
        form = AdvancedSettingsForm(instance=page_a_1)
        form._site = site1
        self.assertFalse(form._check_unique_namespace_instance("instance"))

        form = AdvancedSettingsForm(instance=page_a_2)
        form._site = site1
        self.assertTrue(form._check_unique_namespace_instance("instance"))

        form = AdvancedSettingsForm(instance=page_b_1)
        form._site = site2
        self.assertFalse(form._check_unique_namespace_instance("instance"))

        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_page_for_apphook(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_apphook_permissions(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_apphook_permissions_preserves_view_name(self):
        self.create_base_structure(APP_NAME, ['en', 'de'])

        view_names = (
            ('sample-settings', 'sample_view'),
            ('sample-class-view', 'ClassView'),
            ('sample-class-based-view', 'ClassBasedView'),
        )

        with force_language("en"):
            for url_name, view_name in view_names:
                path = reverse(url_name)
                match = resolve(path)
                self.assertEqual(match.func.__name__, view_name)

    def test_apphooks_with_excluded_permissions(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.urls_3')
    def test_get_page_for_apphook_on_preview_or_edit(self):
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

        # Needed because publish button only shows if the page is dirty
        page.set_publisher_state('en', state=PUBLISHER_STATE_DIRTY)

        public_page = page.get_public_object()

        with force_language("en"):
            path = reverse('sample-settings')
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'
            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, public_page.pk)

        with force_language("de"):
            path = reverse('sample-settings')
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'de'
            attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
            self.assertEqual(attached_to_page.pk, public_page.pk)

        with self.login_user_context(superuser):
            with force_language("en"):
                path = reverse('sample-settings')
                request = self.get_request(path + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                request.LANGUAGE_CODE = 'en'
                attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
                self.assertEqual(attached_to_page.pk, page.pk)
            with force_language("de"):
                path = reverse('sample-settings')
                request = self.get_request(path + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                request.LANGUAGE_CODE = 'de'
                attached_to_page = applications_page_check(request, path=path[1:])  # strip leading slash
                self.assertEqual(attached_to_page.pk, page.pk)

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_root_page_for_apphook_with_instance_namespace(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_child_page_for_apphook_with_instance_namespace(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_sub_page_for_apphook_with_implicit_current_app(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_default_language_changer_with_implicit_current_app(self):
        self.create_base_structure(NS_APP_NAME, ['en', 'de'], 'namespaced_app_ns')
        self.reload_urls()
        with force_language("en"):
            path = reverse('namespaced_app_ns:translated-url')
        request = self.get_request(path)
        request.LANGUAGE_CODE = 'en'

        url = DefaultLanguageChanger(request)('en')
        self.assertEqual(url, path)

        url = DefaultLanguageChanger(request)('de')
        self.assertEqual(url, '/de%s' % path[3:].replace('/page', '/Seite'))
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_i18n_apphook_with_explicit_current_app(self):
        self.apphook_clear()
        titles = self.create_base_structure(NS_APP_NAME, ['en', 'de'], 'instance_1')
        public_de_title = titles[1]
        de_title = Title.objects.get(page=public_de_title.page.publisher_draft, language="de")
        de_title.slug = "de"
        de_title.save()
        de_title.page.publish('de')

        self.reload_urls()
        self.apphook_clear()

        page2 = create_page("page2",
                            "nav_playground.html",
                            language="en",
                            created_by=self.superuser,
                            published=True,
                            parent=de_title.page.get_parent_page(),
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_apphook_include_extra_parameters(self):
        self.create_base_structure(NS_APP_NAME, ['en', 'de'], 'instance_1')
        with force_language("en"):
            path = reverse('namespaced_app_ns:extra_second')
        request = self.get_request(path)
        request.LANGUAGE_CODE = 'en'
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sampleapp/extra.html')
        self.assertContains(response, 'someopts')

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_sub_page_for_apphook_with_explicit_current_app(self):
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
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_include_urlconf(self):
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

        self.apphook_clear()

    @override_settings(CMS_PERMISSION=False, ROOT_URLCONF='cms.test_utils.project.urls_2')
    def test_apphook_breaking_under_home_with_new_path_caching(self):
        home = self.create_homepage("home", "nav_playground.html", "en", published=True)
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

    @override_settings(ROOT_URLCONF='cms.test_utils.project.urls')
    def test_apphook_urlpattern_order(self):
        # this one includes the actual cms.urls, so it can be tested if
        # they are loaded in the correct order (the cms page pattern must be last)
        # (the other testcases replicate the inclusion code and thus don't test this)
        self.create_base_structure(APP_NAME, 'en')
        path = reverse('extra_second')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sampleapp/extra.html')
        self.assertContains(response, "test included urlconf")

    @override_settings(ROOT_URLCONF='cms.test_utils.project.urls')
    def test_apphooks_receive_url_params(self):
        # make sure that urlparams actually reach the apphook views
        self.create_base_structure(APP_NAME, 'en')
        path = reverse('sample-params', kwargs=dict(my_params='is-my-param-really-in-the-context-QUESTIONMARK'))
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sampleapp/home.html')
        self.assertContains(response, 'my_params: is-my-param-really-in-the-context-QUESTIONMARK')

    @override_settings(ROOT_URLCONF='cms.test_utils.project.third_urls_for_apphook_tests')
    def test_multiple_apphooks(self):
        # test for #1538
        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        create_page("home", "nav_playground.html", "en", created_by=superuser, published=True, )
        create_page("apphook1-page", "nav_playground.html", "en",
                    created_by=superuser, published=True, apphook="SampleApp")
        create_page("apphook2-page", "nav_playground.html", "en",
                    created_by=superuser, published=True, apphook="SampleApp2")

        reverse('sample-root')
        reverse('sample2-root')
        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.fourth_urls_for_apphook_tests')
    def test_apphooks_return_urls_directly(self):
        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = create_page("apphooked3-page", "nav_playground.html", "en",
                           created_by=superuser, published=True, apphook="SampleApp3")
        self.assertTrue(page.publish('en'))
        self.reload_urls()

        path = reverse('sample3-root')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sample App 3 Response')
        self.apphook_clear()

    def test_apphook_pool_register_returns_apphook(self):
        @apphook_pool.register
        class TestApp(CMSApp):
            name = "Test App"
        self.assertIsNotNone(TestApp)

        # Now test the quick return codepath, when apphooks is not empty
        apphook_pool.apphooks.append("foo")

        @apphook_pool.register
        class TestApp2(CMSApp):
            name = "Test App 2"
        self.assertIsNotNone(TestApp2)

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_apphook_csrf_exempt_endpoint(self):
        self.create_base_structure(NS_APP_NAME, 'en', 'instance_ns')

        client = self.client_class(enforce_csrf_checks=True)

        with force_language("en"):
            path = reverse('namespaced_app_ns:sample-exempt')

        response = client.post(path)

        # Assert our POST request went through
        self.assertEqual(response.status_code, 200)

        with force_language("en"):
            path = reverse('namespaced_app_ns:sample-account')

        response = client.post(path)

        # Assert our POST request did not go through
        self.assertEqual(response.status_code, 403)

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_toolbar_current_app_namespace(self):
        self.create_base_structure(NS_APP_NAME, 'en', 'instance_ns')
        with force_language("en"):
            path = reverse('namespaced_app_ns:sample-settings')
        request = self.get_request(path)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].is_current_app)
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].is_current_app)

        # Testing a decorated view
        with force_language("en"):
            path = reverse('namespaced_app_ns:sample-exempt')
        request = self.get_request(path)
        toolbar = CMSToolbar(request)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].app_path,
                         'cms.test_utils.project.sampleapp')
        self.assertTrue(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].is_current_app)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].app_path,
                         'cms.test_utils.project.sampleapp')
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].is_current_app)

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_toolbar_current_app_apphook_with_implicit_current_app(self):
        self.create_base_structure(NS_APP_NAME, 'en', 'namespaced_app_ns')
        with force_language("en"):
            path = reverse('namespaced_app_ns:current-app')
        request = self.get_request(path)
        toolbar = CMSToolbar(request)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].app_path,
                         'cms.test_utils.project.sampleapp')
        self.assertTrue(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].is_current_app)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].app_path,
                         'cms.test_utils.project.sampleapp')
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].is_current_app)

    @override_settings(ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls')
    def test_toolbar_no_namespace(self):
        # Test with a basic application with no defined app_name and no namespace
        self.create_base_structure(APP_NAME, 'en')
        path = reverse('detail', kwargs={'id': 20})
        request = self.get_request(path)
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].is_current_app)
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].is_current_app)
        self.assertTrue(toolbar.toolbars['cms.test_utils.project.placeholderapp.cms_toolbars.Example1Toolbar'].is_current_app)

    @override_settings(ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls')
    def test_toolbar_multiple_supported_apps(self):
        # Test with a basic application with no defined app_name and no namespace
        self.create_base_structure(APP_NAME, 'en')
        path = reverse('detail', kwargs={'id': 20})
        request = self.get_request(path)
        toolbar = CMSToolbar(request)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].app_path,
                         'cms.test_utils.project.placeholderapp')
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.sampleapp.cms_toolbars.CategoryToolbar'].is_current_app)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].app_path,
                         'cms.test_utils.project.placeholderapp')
        self.assertFalse(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyTitleExtensionToolbar'].is_current_app)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyPageExtensionToolbar'].app_path,
                         'cms.test_utils.project.placeholderapp')
        self.assertTrue(toolbar.toolbars['cms.test_utils.project.extensionapp.cms_toolbars.MyPageExtensionToolbar'].is_current_app)
        self.assertEqual(toolbar.toolbars['cms.test_utils.project.placeholderapp.cms_toolbars.Example1Toolbar'].app_path,
                         'cms.test_utils.project.placeholderapp')
        self.assertTrue(toolbar.toolbars['cms.test_utils.project.placeholderapp.cms_toolbars.Example1Toolbar'].is_current_app)

    @override_settings(
        CMS_APPHOOKS=['cms.test_utils.project.placeholderapp.cms_apps.Example1App'],
        ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls',
    )
    def test_toolbar_staff(self):
        # Test that the toolbar contains edit mode switcher if placeholders are available
        apphooks = (
            'cms.test_utils.project.placeholderapp.cms_apps.Example1App',
        )

        switcher_id = 'Mode Switcher'

        with self.settings(CMS_APPHOOKS=apphooks, ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls'):
            self.create_base_structure('Example1App', 'en')
            ex1 = Example1.objects.create(char_1='1', char_2='2', char_3='3', char_4='4', date_field=now())
            path = reverse('example_detail', kwargs={'pk': ex1.pk})

            self.user = self._create_user('admin_staff', True, True)
            with self.login_user_context(self.user):
                response = self.client.get(path+"?edit")

            request = response.context['request']
            toolbar = request.toolbar
            items = toolbar.get_right_items()
            switchers = [item.identifier for item in items
                         if getattr(item, 'identifier', '') == switcher_id]
            self.assertEqual(len(switchers), 1)

            self.user = self._create_user('staff', True, False)
            with self.login_user_context(self.user):
                response = self.client.get(path+"?edit")

            request = response.context['request']
            request.user = get_user_model().objects.get(pk=self.user.pk)
            toolbar = request.toolbar
            items = toolbar.get_right_items()
            switchers = [item.identifier for item in items
                         if getattr(item, 'identifier', '') == switcher_id]
            self.assertEqual(len(switchers), 0)

            self.user.user_permissions.add(Permission.objects.get(codename='change_example1'))
            with self.login_user_context(self.user):
                response = self.client.get(path+"?edit")

            request = response.context['request']
            request.user = get_user_model().objects.get(pk=self.user.pk)
            toolbar = request.toolbar
            items = toolbar.get_right_items()
            switchers = [item.identifier for item in items
                         if getattr(item, 'identifier', '') == switcher_id]
            self.assertEqual(len(switchers), 0)

            self.user.user_permissions.add(Permission.objects.get(codename='use_structure'))
            with self.login_user_context(self.user):
                response = self.client.get(path + "?edit")

            request = response.context['request']
            request.user = get_user_model().objects.get(pk=self.user.pk)
            toolbar = request.toolbar
            items = toolbar.get_right_items()
            switchers = [item.identifier for item in items
                         if getattr(item, 'identifier', '') == switcher_id]
            self.assertEqual(len(switchers), 1)

            self.user = None

    def test_page_edit_redirect_models(self):
        apphooks = (
            'cms.test_utils.project.placeholderapp.cms_apps.Example1App',
        )
        ex1 = Example1.objects.create(char_1="char_1", char_2="char_2",
                                      char_3="char_3", char_4="char_4")
        with self.settings(CMS_APPHOOKS=apphooks, ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls'):
            self.create_base_structure('Example1App', 'en')
            url = admin_reverse('cms_page_resolve')
            self.user = self._create_user('admin_staff', True, True)
            with self.login_user_context(self.user):
                # parameters - non page object
                response = self.client.post(url, {'pk': ex1.pk, 'model': 'placeholderapp.example1'})
                self.assertEqual(response.content.decode('utf-8'), ex1.get_absolute_url())

    def test_nested_apphooks_urls(self):
        # make sure that urlparams actually reach the apphook views
        with self.settings(ROOT_URLCONF='cms.test_utils.project.urls'):
            self.apphook_clear()

            superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
            create_page("home", "nav_playground.html", "en", created_by=superuser, published=True, )
            parent_page = create_page("parent-apphook-page", "nav_playground.html", "en",
                                      created_by=superuser, published=True, apphook="ParentApp")
            create_page("child-apphook-page", "nav_playground.html", "en", parent=parent_page,
                        created_by=superuser, published=True, apphook="ChildApp")

            parent_app_path = reverse('parentapp_view', kwargs={'path': 'parent/path/'})
            child_app_path = reverse('childapp_view', kwargs={'path': 'child-path/'})

            # Ensure the page structure is ok before getting responses
            self.assertEqual(parent_app_path, '/en/parent-apphook-page/parent/path/')
            self.assertEqual(child_app_path, '/en/parent-apphook-page/child-apphook-page/child-path/')

            # Get responses for both paths and ensure that the right view will answer
            response = self.client.get(parent_app_path)
            self.assertContains(response, 'parent app content', status_code=200)

            response = self.client.get(child_app_path)
            self.assertContains(response, 'child app content', status_code=200)

            self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_apps(self):
        """
        Check that urlconf are dynamically loaded according to the different page the apphook is
        attached to
        """
        titles = self.create_base_structure('VariableUrlsApp', ['en', 'de'])
        titles[0].page.reverse_id = 'page1'
        titles[0].page.save()

        self.reload_urls()

        # only one urlconf is configured given that only one page is created
        with force_language('de'):
            reverse('extra_first')
            with self.assertRaises(NoReverseMatch):
                reverse('sample2-root')

        self.reload_urls()
        self.apphook_clear()

        page2 = create_page('page2', 'nav_playground.html',
                            'en', created_by=self.superuser, published=True,
                            parent=titles[0].page.get_parent_page().get_draft_object(),
                            apphook='VariableUrlsApp', reverse_id='page2')
        create_title('de', 'de_title', page2, slug='slug')
        page2.publish('de')

        self.reload_urls()

        with force_language('de'):
            reverse('sample2-root')
            reverse('extra_first')

        self.apphook_clear()

    @override_settings(ROOT_URLCONF='cms.test_utils.project.second_urls_for_apphook_tests')
    def test_get_menus(self):
        """
        Check that menus are dynamically loaded according to the different page the apphook is
        attached to
        """
        titles = self.create_base_structure('VariableUrlsApp', ['en', 'de'])
        titles[0].page.reverse_id = 'page1'
        titles[0].page.save()
        cache.clear()
        self.reload_urls()
        menu_pool.discover_menus()
        cache.clear()

        request = self.get_request('/')
        renderer = menu_pool.get_renderer(request)
        with mock.patch("menus.menu_pool.logger.error"):
            nodes = renderer.get_nodes()
        nodes_urls = [node.url for node in nodes]
        self.assertTrue(reverse('sample-account') in nodes_urls)
        self.assertFalse('/en/child_page/page2/' in nodes_urls)

        self.reload_urls()
        self.apphook_clear()

        cache.clear()
        self.reload_urls()

        page2 = create_page('page2', 'nav_playground.html',
                            'en', created_by=self.superuser, published=True,
                            parent=titles[0].page.get_parent_page().get_draft_object(),
                            in_navigation=True,
                            apphook='VariableUrlsApp', reverse_id='page2')
        create_title('de', 'de_title', page2, slug='slug')
        page2.publish('de')
        request = self.get_request('/page2/')
        renderer = menu_pool.get_renderer(request)
        nodes = renderer.get_nodes()
        nodes_urls = [node.url for node in nodes]
        self.assertTrue(reverse('sample-account') in nodes_urls)
        self.assertTrue(reverse('sample2-root') in nodes_urls)
        self.assertTrue('/static/fresh/' in nodes_urls)

        self.apphook_clear()

    @override_settings(
        CMS_APPHOOKS=['cms.test_utils.project.sampleapp.cms_apps.AppWithNoMenu'],
    )
    def test_menu_node_is_selected_on_app_root(self):
        """
        If a user requests a page with an apphook,
        the menu should mark the node for that page as selected.
        """
        defaults = {
            'language': 'en',
            'published': True,
            'in_navigation': True,
            'template': 'nav_playground.html',
        }
        homepage = create_page('EN-P1', **defaults)
        homepage.set_as_homepage()
        app_root = create_page('EN-P2', apphook='AppWithNoMenu', apphook_namespace='app_with_no_menu', **defaults)

        # Public version
        request = self.get_request(self.get_edit_on_url('/en/en-p2/'))
        request.current_page = get_page(request)
        menu_nodes = menu_pool.get_renderer(request).get_nodes()
        self.assertEqual(len(menu_nodes), 2)
        self.assertEqual(menu_nodes[0].id, homepage.publisher_public_id)
        self.assertEqual(menu_nodes[0].selected, False)
        self.assertEqual(menu_nodes[1].id, app_root.publisher_public_id)
        self.assertEqual(menu_nodes[1].selected, True)

        # Draft version
        with self.login_user_context(self.get_superuser()):
            request = self.get_request(self.get_edit_on_url('/en/en-p2/'))
            request.current_page = get_page(request)
            menu_nodes = menu_pool.get_renderer(request).get_nodes()
            self.assertEqual(len(menu_nodes), 2)
            self.assertEqual(menu_nodes[0].id, homepage.pk)
            self.assertEqual(menu_nodes[0].selected, False)
            self.assertEqual(menu_nodes[1].id, app_root.pk)
            self.assertEqual(menu_nodes[1].selected, True)

    @override_settings(
        CMS_APPHOOKS=['cms.test_utils.project.sampleapp.cms_apps.AppWithNoMenu'],
    )
    def test_menu_node_is_selected_on_app_sub_path(self):
        """
        If a user requests a path belonging to an apphook,
        the menu should mark the node for the apphook page as selected.
        """
        # Refs - https://github.com/divio/django-cms/issues/6336
        defaults = {
            'language': 'en',
            'published': True,
            'in_navigation': True,
            'template': 'nav_playground.html',
        }
        homepage = create_page('EN-P1', **defaults)
        homepage.set_as_homepage()
        app_root = create_page('EN-P2', apphook='AppWithNoMenu', apphook_namespace='app_with_no_menu', **defaults)

        # Public version
        request = self.get_request(self.get_edit_on_url('/en/en-p2/settings/'))
        request.current_page = get_page(request)
        menu_nodes = menu_pool.get_renderer(request).get_nodes()
        self.assertEqual(len(menu_nodes), 2)
        self.assertEqual(menu_nodes[0].id, homepage.publisher_public_id)
        self.assertEqual(menu_nodes[0].selected, False)
        self.assertEqual(menu_nodes[1].id, app_root.publisher_public_id)
        self.assertEqual(menu_nodes[1].selected, True)

        # Draft version
        with self.login_user_context(self.get_superuser()):
            request = self.get_request(self.get_edit_on_url('/en/en-p2/settings/'))
            request.current_page = get_page(request)
            menu_nodes = menu_pool.get_renderer(request).get_nodes()
            self.assertEqual(len(menu_nodes), 2)
            self.assertEqual(menu_nodes[0].id, homepage.pk)
            self.assertEqual(menu_nodes[0].selected, False)
            self.assertEqual(menu_nodes[1].id, app_root.pk)
            self.assertEqual(menu_nodes[1].selected, True)


class ApphooksPageLanguageUrlTestCase(CMSTestCase):
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
        self.apphook_clear()

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

        self.apphook_clear()
        superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = self.create_homepage("home", "nav_playground.html", "en", created_by=superuser)
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
        self.assertEqual(url, '/en/child_page/child_child_page/extra_1/')

        self.apphook_clear()
