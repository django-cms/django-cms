import re
import sys

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.http import Http404
from django.template import Variable
from django.test.utils import override_settings
from django.urls import clear_url_caches

from cms.api import create_page, create_title, publish_page
from cms.models import PagePermission, UserSettings, Placeholder
from cms.page_rendering import _handle_no_page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.utils.conf import get_cms_setting
from cms.views import details
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
        super(ViewTests, self).tearDown()
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
        page = create_page("page2", "nav_playground.html", "en", published=True)
        with self.settings(CMS_APPHOOKS=apphooks):
            self.apphook_clear()
            response = self.client.get(page.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            self.apphook_clear()

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
        url = three.get_absolute_url()
        request = self.get_request(url)
        response = details(request, three.get_path())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], redirect_three)

    def test_redirect_to_self(self):
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect='/one/')
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, one.get_path())
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_self_with_host(self):
        one = create_page("one", "nav_playground.html", "en", published=True,
                          redirect='http://testserver/en/one/')
        url = one.get_absolute_url()
        request = self.get_request(url)
        response = details(request, one.get_path())
        self.assertEqual(response.status_code, 200)

    def test_redirect_with_toolbar(self):
        page = create_page("one", "nav_playground.html", "en", published=True,
                    redirect='/en/page2')
        page_url = page.get_absolute_url()
        page_edit_on_url = self.get_edit_on_url(page_url)

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_on_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'This page has no preview')

            self.client.get(page_edit_on_url)
            response = self.client.get(self.get_edit_off_url(page_url))
            self.assertEqual(response.status_code, 302)

            self.client.get(page_edit_on_url)
            response = self.client.get(self.get_obj_structure_url(page_url))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'This page has no preview')

            self.client.get(page_edit_on_url)
            response = self.client.get(self.get_toolbar_disable_url(page_url))
            self.assertEqual(response.status_code, 302)

    def test_login_required(self):
        self.create_homepage("page", "nav_playground.html", "en", published=True, login_required=True)
        plain_url = '/accounts/'
        login_rx = re.compile("%s\?(signin=|next=/en/)&" % plain_url)
        with self.settings(LOGIN_URL=plain_url + '?signin'):
            request = self.get_request('/en/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))
        login_rx = re.compile("%s\?(signin=|next=/)&" % plain_url)
        with self.settings(USE_I18N=False, LOGIN_URL=plain_url + '?signin'):
            request = self.get_request('/')
            response = details(request, '')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(login_rx.search(response['Location']))

    def test_edit_permission(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        page_url = page.get_absolute_url()
        # Anon user
        response = self.client.get(self.get_edit_on_url(page_url))
        self.assertNotContains(response, "cms_toolbar-item-switch-save-edit", 200)

        # Superuser
        user = self.get_superuser()
        with self.login_user_context(user):
            response = self.client.get(self.get_edit_on_url(page_url))
        self.assertContains(response, "cms-toolbar-item-switch-save-edit", 1, 200)

        # Admin but with no permission
        user = self.get_staff_user_with_no_permissions()
        user.user_permissions.add(Permission.objects.get(codename='change_page'))

        with self.login_user_context(user):
            response = self.client.get(self.get_edit_on_url(page_url))
        self.assertNotContains(response, "cms-toolbar-item-switch-save-edit", 200)

        PagePermission.objects.create(can_change=True, user=user, page=page)
        with self.login_user_context(user):
            response = self.client.get(self.get_edit_on_url(page_url))
        self.assertContains(response, "cms-toolbar-item-switch-save-edit", 1, 200)

    def test_toolbar_switch_urls(self):
        user = self.get_superuser()
        user_settings = UserSettings(language="en", user=user)
        placeholder = Placeholder(slot="clipboard")
        placeholder.save()
        user_settings.clipboard = placeholder
        user_settings.save()

        page = create_page("page", "nav_playground.html", "en", published=True)
        create_title("fr", "french home", page)
        publish_page(page, user, "fr")

        page.set_as_homepage()

        edit_on = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        edit_off = get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')

        with self.login_user_context(user):
            response = self.client.get("/fr/?{}".format(edit_on))
            expected = """
                <a href="?structure" class="cms-btn cms-btn-disabled" title="Toggle structure"
                data-cms-structure-btn='{ "url": "/fr/?structure", "name": "Structure" }'
                data-cms-content-btn='{ "url": "/fr/?edit", "name": "Content" }'>
                <span class="cms-icon cms-icon-plugins"></span></a>
            """
            self.assertContains(
                response,
                expected,
                count=1,
                html=True,
            )
            self.assertContains(
                response,
                '<a class="cms-btn cms-btn-switch-save" href="/fr/?preview&{}">'
                '<span>View published</span></a>'.format(edit_off),
                count=1,
                html=True,
            )
            response = self.client.get("/fr/?preview&{}".format(edit_off))
            self.assertContains(
                response,
                expected,
                count=1,
                html=True,
            )
            self.assertContains(
                response,
                '<a class="cms-btn cms-btn-action cms-btn-switch-edit" href="/fr/?{}">Edit</a>'.format(edit_on),
                count=1,
                html=True,
            )

    def test_incorrect_slug_for_language(self):
        """
        Test details view when page slug and current language don't match.
        In this case we refer to the user's current language and the page slug we have for that language.
        """
        create_page("home", "nav_playground.html", "en", published=True)
        cms_page = create_page("stevejobs", "nav_playground.html", "en", published=True)
        create_title("de", "jobs", cms_page)
        cms_page.publish('de')
        response = self.client.get('/de/stevejobs/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/de/jobs/')


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
        page = self.create_homepage("page", page_template, "en", published=True)
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
            with self.assertNumQueries(FuzzyInt(13, 26)) as context:
                response = self.client.get("/en/page-2/")
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, page_template)
                num_queries_page = len(context.captured_queries)
        cache.clear()
        menu_pool.clear()
        page_2.template = 'INHERIT'
        page_2.save()
        page_2.publish('en')
        with self.settings(**original_context):
            # One query more triggered as page inherits template from ancestor
            with self.assertNumQueries(num_queries_page + 1):
                response = self.client.get("/en/page-2/")
                template = Variable('CMS_TEMPLATE').resolve(response.context)
                self.assertEqual(template, page_template)
