import re
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.template import Variable
from django.test.utils import override_settings
from django.urls import clear_url_caches, reverse
from django.utils.translation import override as force_language

from cms import api
from cms.api import create_page, create_page_content
from cms.middleware.toolbar import ToolbarMiddleware
from cms.models import PageContent, PagePermission, Placeholder, UserSettings
from cms.page_rendering import _handle_no_page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_preview_url,
    get_object_structure_url,
)
from cms.utils.conf import get_cms_setting
from cms.utils.page import get_page_from_request
from cms.utils.urlutils import admin_reverse
from cms.views import details, login, render_object_structure
from menus.menu_pool import menu_pool

APP_NAME = 'SampleApp'
APP_MODULE = "cms.test_utils.project.sampleapp.cms_apps"


@override_settings(
    CMS_PERMISSION=True,
    ROOT_URLCONF='cms.test_utils.project.urls',
)
class ViewTests(CMSTestCase):

    def setUp(self):
        clear_url_caches()

    def tearDown(self):
        super().tearDown()
        clear_url_caches()

    def test_welcome_screen_debug_on(self):
        clear_url_caches()
        with self.settings(DEBUG=True):
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.template_name, 'cms/welcome.html')

    def test_welcome_screen_debug_off(self):
        with self.settings(DEBUG=False):
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.template_name, 'cms/welcome.html')

    def test_handle_no_page(self):
        """
        Test handle nopage correctly works with DEBUG=True
        """
        request = self.get_request('/not-existing/')
        self.assertRaises(Http404, _handle_no_page, request)

    def test_handle_no_page_for_root_url(self):
        """
        Test if _handle_no_page correctly works for root url
        """
        request = self.get_request('/en/')
        response = _handle_no_page(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin:cms_pagecontent_changelist'))

    def test_handle_no_page_for_rool_url_no_homepage(self):
        """
        Test details view when visiting root and homepage doesn't exist
        """
        create_page("one", "nav_playground.html", "en")
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 302)

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
        page = create_page("page2", "nav_playground.html", "en")
        with self.settings(CMS_APPHOOKS=apphooks):
            self.apphook_clear()
            response = self.client.get(page.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            self.apphook_clear()

    def test_external_redirect(self):
        # test external redirect
        redirect_one = 'https://www.django-cms.org/'
        one = create_page("one", "nav_playground.html", "en",
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
        one = create_page("one", "nav_playground.html", "en",
                          redirect=redirect_one)
        two = create_page("two", "nav_playground.html", "en", parent=one,
                          redirect=redirect_two)
        url = two.get_absolute_url()
        request = self.get_request(url)
        response = details(request, two.get_path('en'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')

    def test_internal_forced_redirect(self):
        # test internal forced language redirect
        redirect_one = 'https://www.django-cms.org/'
        redirect_three = '/en/'
        one = create_page("one", "nav_playground.html", "en",
                          redirect=redirect_one)
        three = create_page("three", "nav_playground.html", "en", parent=one,
                            redirect=redirect_three)
        url = three.get_absolute_url()
        request = self.get_request(url)
        response = details(request, three.get_path('en'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_three)

    def test_redirect_to_self(self):
        one = create_page("one", "nav_playground.html", "en",
                          redirect='/one/')
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, one.get_path('en'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_self_with_host(self):
        one = create_page("one", "nav_playground.html", "en",
                          redirect='http://testserver/en/one/')
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, one.get_path('en'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_not_preserving_query_parameters(self):
        # test redirect checking that the query parameters aren't preserved
        redirect = '/en/'
        one = create_page("one", "nav_playground.html", "en", redirect=redirect)
        url = one.get_absolute_url()
        params = "?param_name=param_value"
        request = self.get_request(url + params)
        response = details(request, one.get_path(language="en"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect)

    @override_settings(CMS_REDIRECT_PRESERVE_QUERY_PARAMS=True)
    def test_redirect_preserving_query_parameters(self):
        # test redirect checking that query parameters are preserved
        redirect = '/en/'
        one = create_page("one", "nav_playground.html", "en", redirect=redirect)
        url = one.get_absolute_url()
        params = "?param_name=param_value"
        request = self.get_request(url + params)
        response = details(request, one.get_path(language="en"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect + params)

    @override_settings(CMS_REDIRECT_TO_LOWERCASE_SLUG=True)
    def test_redirecting_to_lowercase_slug(self):
        redirect = '/en/one/'
        one = create_page("one", "nav_playground.html", "en", redirect=redirect)
        url = reverse('pages-details-by-slug', kwargs={"slug": "One"})
        request = self.get_request(url)
        response = details(request, one.get_path(language="en"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect)

    def test_login_required(self):
        self.create_homepage("page", "nav_playground.html", "en", login_required=True)
        plain_url = '/accounts/'
        login_rx = re.compile("%s\\?(signin=|next=/en/)&" % plain_url)
        with self.settings(LOGIN_URL=plain_url + '?signin'):
            request = self.get_request('/en/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))
        login_rx = re.compile("%s\\?(signin=|next=/)&" % plain_url)
        with self.settings(USE_I18N=False, LOGIN_URL=plain_url + '?signin'):
            request = self.get_request('/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))

    def test_edit_permission(self):
        page = create_page("page", "nav_playground.html", "en")
        page_content = self.get_page_title_obj(page)
        page_preview_url = get_object_preview_url(page_content)
        # Anon user
        response = self.client.get(page_preview_url)
        self.assertRedirects(response, f'/en/admin/login/?next={page_preview_url}')

        # Superuser
        user = self.get_superuser()
        with self.login_user_context(user):
            response = self.client.get(page_preview_url)
        toolbar = response.wsgi_request.toolbar
        edit_button = toolbar.get_right_items()[2].buttons[0]
        self.assertEqual(edit_button.name, 'Edit')
        self.assertEqual(edit_button.url, get_object_edit_url(page_content))
        self.assertEqual(
            edit_button.extra_classes,
            ['cms-btn', 'cms-btn-action', 'cms-btn-switch-edit']
        )

        # Admin but with no permission
        user = self.get_staff_user_with_no_permissions()
        user.user_permissions.add(Permission.objects.get(codename='change_page'))

        with self.login_user_context(user):
            response = self.client.get(page_preview_url)
        toolbar = response.wsgi_request.toolbar
        self.assertEqual(len(toolbar.get_right_items()), 2)  # Only has Create button and color switch

        PagePermission.objects.create(can_change=True, user=user, page=page)
        with self.login_user_context(user):
            response = self.client.get(page_preview_url)
        toolbar = response.wsgi_request.toolbar
        edit_button = toolbar.get_right_items()[2].buttons[0]
        self.assertEqual(edit_button.name, 'Edit')
        self.assertEqual(edit_button.url, get_object_edit_url(page_content))
        self.assertEqual(
            edit_button.extra_classes,
            ['cms-btn', 'cms-btn-action', 'cms-btn-switch-edit']
        )

    def test_toolbar_switch_urls(self):
        from django.utils.translation import gettext_lazy as _

        user = self.get_superuser()
        user_settings = UserSettings(language="en", user=user)
        placeholder = Placeholder(slot="clipboard")
        placeholder.save()
        user_settings.clipboard = placeholder
        user_settings.save()

        page = create_page("page", "nav_playground.html", "en")
        page_content = create_page_content("fr", "french home", page)

        page.set_as_homepage()

        with self.login_user_context(user), force_language('fr'):
            edit_url = get_object_edit_url(page_content, language='fr')
            preview_url = get_object_preview_url(page_content, language='fr')
            structure_url = get_object_structure_url(page_content, language='fr')

            response = self.client.get(edit_url)
            expected = """
                <a href="%s" class="cms-btn cms-btn-disabled" title="Toggle structure"
                data-cms-structure-btn='{ "url": "%s", "name": "Structure" }'
                data-cms-content-btn='{ "url": "%s", "name": "Content" }'>
                <span class="cms-icon cms-icon-plugins"></span></a>
            """ % (
                structure_url,
                structure_url,
                edit_url,
            )
            self.assertContains(
                response,
                expected,
                count=1,
                html=True,
            )
            toolbar = response.wsgi_request.toolbar
            self.assertEqual(len(toolbar.get_right_items()[2].buttons), 1)
            preview_button = toolbar.get_right_items()[2].buttons[0]
            self.assertEqual(preview_button.name, _('Preview'))
            self.assertEqual(preview_button.url, preview_url)
            self.assertEqual(
                preview_button.extra_classes,
                ['cms-btn', 'cms-btn-switch-save']
            )

            response = self.client.get(preview_url)
            self.assertContains(
                response,
                expected,
                count=1,
                html=True,
            )
            toolbar = response.wsgi_request.toolbar
            self.assertEqual(len(toolbar.get_right_items()[2].buttons), 1)
            edit_button = toolbar.get_right_items()[2].buttons[0]
            self.assertEqual(edit_button.name, _('Edit'))
            self.assertEqual(edit_button.url, edit_url)
            self.assertEqual(
                edit_button.extra_classes,
                ['cms-btn', 'cms-btn-action', 'cms-btn-switch-edit']
            )

    def test_incorrect_slug_for_language(self):
        """
        Test details view when page slug and current language don't match.
        In this case we refer to the user's current language and the page slug we have for that language.
        """
        create_page("home", "nav_playground.html", "en")
        cms_page = create_page("stevejobs", "nav_playground.html", "en")
        create_page_content("de", "jobs", cms_page)
        response = self.client.get('/de/stevejobs/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/de/jobs/')

    def test_page_sanitisation_xss_attack(self):
        """
            When sending a request the CMS uses get_page_from_request to return the appropriate page.
            None should be returned
        """
        request = self.get_request("/")
        request.path_info = "<script>alert('attack!')</script>"

        response = get_page_from_request(request)

        # If this method is passed a parameter which is not a valid primary key
        # for a page object nothing should be returned.
        self.assertEqual(response, None)

    def test_malicious_content_login_request(self):
        username = getattr(self.get_superuser(), get_user_model().USERNAME_FIELD)
        request = self.get_request(
            "/en/admin/login/?q=<script>alert('Attack')</script>",
            post_data={"username": username, "password": username}
        )

        response = login(request)

        self.assertNotIn(response.url, "<script>alert('Attack')</script>")


@override_settings(ROOT_URLCONF='cms.test_utils.project.urls')
class ContextTests(CMSTestCase):

    def test_context_current_page(self):
        """
        Asserts the number of queries triggered by
        `cms.context_processors.cms_settings` and `cms.middleware.page`
        """
        from django.template import context

        page_template = "nav_playground.html"
        original_context = {'TEMPLATES': settings.TEMPLATES}
        page = self.create_homepage("page", page_template, "en")
        page_2 = create_page("page-2", page_template, "en",
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

        # Number of queries when context processor is enabled
        with self.settings(**original_context):
            with self.assertNumQueries(FuzzyInt(0, 17)):
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

        # Number of queries when context processors is enabled
        with self.settings(**original_context):
            with self.assertNumQueries(FuzzyInt(13, 30)) as context:
                response = self.client.get("/en/page-2/")
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, page_template)
                num_queries_page = len(context.captured_queries)
        cache.clear()
        menu_pool.clear()
        page_2.update_translations(template='INHERIT')

        with self.settings(**original_context):
            # One query more triggered as page inherits template from ancestor
            with self.assertNumQueries(num_queries_page + 1):
                response = self.client.get("/en/page-2/")
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, page_template)

class EndpointTests(CMSTestCase):

    def setUp(self) -> None:
        page_template = "simple.html"
        self.page = self.create_homepage("page", page_template, "en")

        self.page_content_en = self.page.get_content_obj()
        self.page_content_fr = create_page_content("fr", "french home", self.page)
        self.content_type = ContentType.objects.get_for_model(PageContent)

        self.client.force_login(self.get_superuser())

    def tearDown(self) -> None:
        self.page.delete()

    def test_render_object_structure(self):
        request = self.get_request("/")
        request.user = self.get_superuser()
        mid = ToolbarMiddleware(lambda req: HttpResponse(""))
        mid(request)
        response = render_object_structure(request, self.content_type.id, self.page_content_en.pk)

        self.assertEqual(request.current_page, self.page)
        self.assertContains(response, '<div class="cms-toolbar">')

    def test_render_object_structure_i18n(self):
        """Structure view shows the page content's language not the request's language."""
        placeholder = self.page.get_placeholders("fr").first()
        self._add_plugin_to_placeholder(placeholder, "TextPlugin", language="fr")
        with force_language("fr"):
            setting, _ = UserSettings.objects.get_or_create(user=self.get_superuser())
            setting.language="fr"
            setting.save()
            structure_endpoint_url = admin_reverse(
                "cms_placeholder_render_object_structure",
                args=(self.content_type.id, self.page_content_fr.pk,)
            )
            response = self.client.get(structure_endpoint_url)
            self.assertContains(response, '<strong>Texte</strong>')

            setting.language = "en"
            setting.save()

            response = self.client.get(structure_endpoint_url)
            self.assertContains(response, '<strong>Text</strong>')
