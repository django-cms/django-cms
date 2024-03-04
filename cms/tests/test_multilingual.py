import copy

from django.contrib.sites.models import Site
from django.test.utils import override_settings
from django.urls import reverse

from cms.api import add_plugin, create_page, create_page_content
from cms.exceptions import LanguageError
from cms.forms.utils import update_site_and_page_choices
from cms.models import EmptyPageContent, PageContent
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import get_cms_setting, get_languages
from menus.menu_pool import menu_pool

TEMPLATE_NAME = 'tests/rendering/base.html'


def get_primary_language(current_site=None):
    """Fetch the first language of the current site settings."""
    current_site = current_site or Site.objects.get_current()
    return get_languages()[current_site.id][0]['code']


def get_secondary_language(current_site=None):
    """Fetch the other language of the current site settings."""
    current_site = current_site or Site.objects.get_current()
    return get_languages()[current_site.id][1]['code']


@override_settings(
    CMS_TEMPLATES=[
        (TEMPLATE_NAME, TEMPLATE_NAME),
        ('extra_context.html', 'extra_context.html'),
        ('nav_playground.html', 'nav_playground.html'),
    ],
)
class MultilingualTestCase(CMSTestCase):

    def test_create_page(self):
        """
        Test that a page can be created
        and that a new language can be created afterwards in the admin pages
        """

        # Create a new page

        # Use the very first language in the list of languages
        # for the current site
        current_site = Site.objects.get_current()
        TESTLANG = get_primary_language(current_site=current_site)
        page_data = self.get_new_page_data_dbfields(
            site=current_site,
            language=TESTLANG
        )

        page = create_page(**page_data)
        content = page.get_content_obj()

        # A title is set?
        self.assertTrue(bool(content))

        # Has correct title and slug after calling save()?
        self.assertEqual(page.get_title(), page_data['title'])
        self.assertEqual(page.get_slug(TESTLANG), page_data['slug'])
        self.assertEqual(page.get_placeholders(TESTLANG).count(), 2)

        # Do stuff using admin pages
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_pagedata_from_dbfields(page_data)

            self.client.post(self.get_page_change_uri(TESTLANG, page), page_data)

            # Create a different language using the edit admin page
            # This test case is bound in actual experience...
            # pull#1604
            TESTLANG2 = get_secondary_language(current_site=current_site)
            page_data2 = page_data.copy()
            page_data2['title'] = 'ein Titel'
            page_data2['slug'] = 'ein-slug'
            page_data2['cms_page'] = page.pk
            page_data2['language'] = TESTLANG2

            # Ensure that the language version is not returned
            # since it does not exist
            self.assertTrue(isinstance(page.get_content_obj(language=TESTLANG2, fallback=False), EmptyPageContent))

            # Now create it
            self.client.post(self.get_page_add_uri(TESTLANG2, page), page_data2)

            page = page.reload()

            # Test the new language version
            page._clear_internal_cache()
            self.assertEqual(page.get_title(language=TESTLANG2), page_data2['title'])
            self.assertEqual(page.get_slug(language=TESTLANG2), page_data2['slug'])

            # Test the default language version (TESTLANG)
            self.assertEqual(page.get_slug(TESTLANG), page_data['slug'])
            self.assertEqual(page.get_title(language=TESTLANG, fallback=False), page_data['title'])

    def test_multilingual_page(self):
        TESTLANG = get_primary_language()
        TESTLANG2 = get_secondary_language()
        page = create_page("mlpage", "nav_playground.html", TESTLANG)
        create_page_content(TESTLANG2, page.get_title(), page, slug=page.get_slug(TESTLANG))
        page.rescan_placeholders(TESTLANG)
        page = self.reload(page)
        page_placeholder_lang_1 = page.get_placeholders(TESTLANG)[0]
        page_placeholder_lang_2 = page.get_placeholders(TESTLANG2)[0]
        add_plugin(page_placeholder_lang_1, "TextPlugin", TESTLANG, body="test")
        add_plugin(page_placeholder_lang_2, "TextPlugin", TESTLANG2, body="test")
        self.assertEqual(page_placeholder_lang_1.get_plugins(language=TESTLANG).count(), 1)
        self.assertEqual(page_placeholder_lang_2.get_plugins(language=TESTLANG2).count(), 1)

    def test_hide_untranslated(self):
        TESTLANG = get_primary_language()
        TESTLANG2 = get_secondary_language()
        page = create_page("mlpage-%s" % TESTLANG, "nav_playground.html", TESTLANG)
        create_page_content(TESTLANG2, "mlpage-%s" % TESTLANG2, page, slug=page.get_slug(TESTLANG))
        create_page("mlpage-2-%s" % TESTLANG, "nav_playground.html", TESTLANG, parent=page)

        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))

        request_1 = self.get_request('/%s/' % TESTLANG, TESTLANG)
        request_2 = self.get_request('/%s/' % TESTLANG2, TESTLANG2)

        request_1_menu_renderer = menu_pool.get_renderer(request_1)
        request_2_menu_renderer = menu_pool.get_renderer(request_2)

        lang_settings[1][1]['hide_untranslated'] = False
        with self.settings(CMS_LANGUAGES=lang_settings):
            request_1_nodes = request_1_menu_renderer.get_menu('CMSMenu').get_nodes(request_1)
            request_2_nodes = request_2_menu_renderer.get_menu('CMSMenu').get_nodes(request_2)
            list_1 = [node.id for node in request_1_nodes]
            list_2 = [node.id for node in request_2_nodes]
            self.assertEqual(list_1, list_2)
            self.assertEqual(len(list_1), 2)

        lang_settings[1][1]['hide_untranslated'] = True
        with self.settings(CMS_LANGUAGES=lang_settings):
            request_1_nodes = request_1_menu_renderer.get_menu('CMSMenu').get_nodes(request_1)
            request_2_nodes = request_2_menu_renderer.get_menu('CMSMenu').get_nodes(request_2)
            list_1 = [node.id for node in request_1_nodes]
            list_2 = [node.id for node in request_2_nodes]
            self.assertNotEqual(list_1, list_2)
            self.assertEqual(len(list_2), 1)
            self.assertEqual(len(list_1), 2)

    def test_frontend_lang(self):
        superuser = self.get_superuser()
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['public'] = False
        with self.settings(CMS_LANGUAGES=lang_settings, LANGUAGE_CODE="en"):
            page = create_page("page1", "nav_playground.html", "en")
            create_page_content("de", page.get_title(), page, slug=page.get_slug('en'))
            page2 = create_page("page2", "nav_playground.html", "en")
            create_page_content("de", page2.get_title(), page2, slug=page2.get_slug('en'))
            page3 = create_page("page2", "nav_playground.html", "en")
            create_page_content("de", page3.get_title(), page3, slug=page3.get_slug('en'))
            create_page("page4", "nav_playground.html", "de")

            page.set_as_homepage()

            # The "en" language is set to public -> False.
            # Because the request is to the root (homepage),
            # the page is redirected to the default language's homepage
            response = self.client.get("/en/")
            self.assertRedirects(response, '/de/')

            # Authenticated requests to a private language
            # will render the page normally as long as the language
            # is available on the page
            with self.login_user_context(superuser):
                response = self.client.get("/en/")
                self.assertEqual(response.status_code, 200)

            response = self.client.get("/en/page2/")
            self.assertEqual(response.status_code, 404)
            response = self.client.get("/de/")
            self.assertEqual(response.status_code, 200)
            response = self.client.get("/de/page2/")
            self.assertEqual(response.status_code, 200)

            # check if the admin can see non-public langs
            with self.login_user_context(self.get_superuser()):
                response = self.client.get("/en/page2/")
                self.assertEqual(response.status_code, 200)
                response = self.client.get("/en/page4/")
                self.assertEqual(response.status_code, 302)
            self.client.logout()
            response = self.client.get("/en/page4/")
            self.assertEqual(response.status_code, 404)

    def test_page_with_invalid_language_for_anon_user(self):
        site_2 = Site.objects.create(id=2, name='example-2.com', domain='example-2.com')
        self.create_homepage(
            "page",
            template='nav_playground.html',
            language="de",
            site=site_2,
        )
        page_2 = create_page(
            "page",
            template='nav_playground.html',
            language="de",
            site=site_2,
        )

        with self.settings(SITE_ID=2, LANGUAGE_CODE='en'):
            # url uses "en" as the request language
            # but the site is configured to use "de" and "fr"
            response = self.client.get('/en/')
            self.assertEqual(response.status_code, 200)
            response = self.client.get('/en/%s/' % page_2.get_path('de'))
            self.assertEqual(response.status_code, 404)

    def test_page_with_invalid_language_for_auth_user(self):
        site_2 = Site.objects.create(id=2, name='example-2.com', domain='example-2.com')
        superuser = self.get_superuser()
        self.create_homepage(
            "page",
            template='nav_playground.html',
            language="de",
            site=site_2,
        )
        page_2 = create_page(
            "page",
            template='nav_playground.html',
            language="de",
            site=site_2,
        )

        with self.settings(SITE_ID=2, LANGUAGE_CODE='en'):
            with self.login_user_context(superuser):
                # url uses "en" as the request language
                # but the site is configured to use "de" and "fr"
                # and no redirect on fallback so cms will render
                # in place
                response = self.client.get('/en/')
                self.assertEqual(response.status_code, 200)
                response = self.client.get('/en/%s/' % page_2.get_path('de'))
                self.assertEqual(response.status_code, 404)

    def test_language_fallback(self):
        """
        Test language fallbacks in details view
        """
        from cms.views import details
        p1 = create_page("page", "nav_playground.html", "en")
        p1.set_as_homepage()

        # There's no "de" translation.
        # Fallbacks are configured.
        # The cms is set to redirect on fallback.
        request = self.get_request('/de/', 'de')
        response = details(request, p1.get_path('en'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')

        # There's no "de" translation.
        # There's no fallbacks configured.
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['fallbacks'] = []
        lang_settings[1][1]['fallbacks'] = []

        with self.settings(CMS_LANGUAGES=lang_settings):
            # No translation for root page
            response = self.client.get("/de/")
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('admin:cms_pagecontent_changelist'))

        with self.settings(CMS_LANGUAGES=lang_settings):
            # No translation for a page other than root
            create_page("page2", "nav_playground.html", "en", slug="page2")
            response = self.client.get("/de/page2/")
            self.assertEqual(response.status_code, 404)

        # There's no "de" translation.
        # Fallbacks are configured.
        # The cms is set to render in place instead of redirecting
        # to the fallback.
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['redirect_on_fallback'] = False
        lang_settings[1][1]['redirect_on_fallback'] = False

        with self.settings(CMS_LANGUAGES=lang_settings):
            response = self.client.get("/de/")
            # as per the comments above, the content should
            # be rendered in place, no redirect should happen
            self.assertEqual(response.status_code, 200)

    def test_no_english_defined(self):
        with self.settings(
            TEMPLATE_CONTEXT_PROCESSORS=[],
            CMS_LANGUAGES={
                1: [
                    {'code': 'de', 'name': 'German', 'public': True, 'fallbacks': []},
                ]},
        ):
            try:
                update_site_and_page_choices(language='en-us')
            except LanguageError:
                self.fail("LanguageError raised")

    def test_wrong_plugin_language(self):
        page = create_page("page", "nav_playground.html", "en")
        ph_en = page.get_placeholders("en").get(slot="body")
        add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        title = PageContent(title="page", language="ru", page=page)
        title.save()
        # add wrong plugin language
        add_plugin(ph_en, "TextPlugin", "ru", body="I'm the second")
        endpoint = page.get_absolute_url()
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
