# -*- coding: utf-8 -*-
import copy

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from cms.api import create_page, create_title, publish_page, add_plugin
from cms.forms.utils import update_site_and_page_choices
from cms.exceptions import LanguageError
from cms.models import Title, EmptyTitle
from cms.test_utils.testcases import (CMSTestCase,
                                      URL_CMS_PAGE_CHANGE_LANGUAGE, URL_CMS_PAGE_PUBLISH)
from cms.utils.conf import get_cms_setting
from cms.utils.conf import get_languages

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
        title = page.get_title_obj()

        # A title is set?
        self.assertTrue(bool(title))

        # Publish and unpublish the page
        page.publish(TESTLANG)

        page.unpublish(TESTLANG)
        page = page.reload()

        # Has correct title and slug after calling save()?
        self.assertEqual(page.get_title(), page_data['title'])
        self.assertEqual(page.get_slug(), page_data['slug'])
        self.assertEqual(page.placeholders.all().count(), 2)

        # Were public instances created?
        title = Title.objects.drafts().get(slug=page_data['slug'])

        # Test that it's the default language
        self.assertEqual(title.language, TESTLANG)

        # Do stuff using admin pages
        superuser = self.get_superuser()
        with self.login_user_context(superuser):

            page_data = self.get_pagedata_from_dbfields(page_data)

            # Publish page using the admin
            page_data['published'] = True
            self.client.post(URL_CMS_PAGE_CHANGE_LANGUAGE % (page.pk, TESTLANG),
                                        page_data)
            self.client.post(URL_CMS_PAGE_PUBLISH % (page.pk, TESTLANG))
            page = page.reload()
            self.assertTrue(page.is_published(TESTLANG))

            # Create a different language using the edit admin page
            # This test case is bound in actual experience...
            # pull#1604
            page_data2 = page_data.copy()
            page_data2['title'] = 'ein Titel'
            page_data2['slug'] = 'ein-slug'
            TESTLANG2 = get_secondary_language(current_site=current_site)
            page_data2['language'] = TESTLANG2

            # Ensure that the language version is not returned
            # since it does not exist
            self.assertTrue(isinstance(page.get_title_obj(language=TESTLANG2, fallback=False), EmptyTitle))

            # Now create it
            self.client.post(URL_CMS_PAGE_CHANGE_LANGUAGE % (page.pk, TESTLANG2),
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

    def test_multilingual_page(self):
        TESTLANG = get_primary_language()
        TESTLANG2 = get_secondary_language()
        page = create_page("mlpage", "nav_playground.html", TESTLANG)
        create_title(TESTLANG2, page.get_title(), page, slug=page.get_slug())
        page.rescan_placeholders()
        page = self.reload(page)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", TESTLANG2, body="test")
        add_plugin(placeholder, "TextPlugin", TESTLANG, body="test")
        self.assertEqual(placeholder.get_plugins(language=TESTLANG2).count(), 1)
        self.assertEqual(placeholder.get_plugins(language=TESTLANG).count(), 1)
        user = get_user_model().objects.create_superuser('super', 'super@django-cms.org', 'super')
        page = publish_page(page, user, TESTLANG)
        page = publish_page(page, user, TESTLANG2)
        public = page.publisher_public
        placeholder = public.placeholders.all()[0]
        self.assertEqual(placeholder.get_plugins(language=TESTLANG2).count(), 1)
        self.assertEqual(placeholder.get_plugins(language=TESTLANG).count(), 1)

    def test_hide_untranslated(self):
        TESTLANG = get_primary_language()
        TESTLANG2 = get_secondary_language()
        page = create_page("mlpage-%s" % TESTLANG, "nav_playground.html", TESTLANG)
        create_title(TESTLANG2, "mlpage-%s" % TESTLANG2, page, slug=page.get_slug())
        page.publish(TESTLANG)
        page.publish(TESTLANG2)
        page2 = create_page("mlpage-2-%s" % TESTLANG, "nav_playground.html", TESTLANG, parent=page)
        page2.publish(TESTLANG)

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
            create_title("de", page.get_title(), page, slug=page.get_slug())
            page2 = create_page("page2", "nav_playground.html", "en")
            create_title("de", page2.get_title(), page2, slug=page2.get_slug())
            page3 = create_page("page2", "nav_playground.html", "en")
            create_title("de", page3.get_title(), page3, slug=page3.get_slug())
            page4 = create_page("page4", "nav_playground.html", "de")
            page.publish('en')
            page.publish('de')
            page2.publish('en')
            page2.publish('de')
            page3.publish('de')
            page3.publish('en')
            page4.publish('de')

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
            published=True,
            site=site_2,
        )
        page_2 = create_page(
            "page",
            template='nav_playground.html',
            language="de",
            published=True,
            site=site_2,
        )

        with self.settings(SITE_ID=2, LANGUAGE_CODE='en'):
            # url uses "en" as the request language
            # but the site is configured to use "de" and "fr"
            response = self.client.get('/en/')
            self.assertRedirects(response, '/de/')
            response = self.client.get('/en/%s/' % page_2.get_path('de'))
            self.assertEqual(response.status_code, 404)

    def test_page_with_invalid_language_for_auth_user(self):
        site_2 = Site.objects.create(id=2, name='example-2.com', domain='example-2.com')
        superuser = self.get_superuser()
        self.create_homepage(
            "page",
            template='nav_playground.html',
            language="de",
            published=True,
            site=site_2,
        )
        page_2 = create_page(
            "page",
            template='nav_playground.html',
            language="de",
            published=True,
            site=site_2,
        )

        with self.settings(SITE_ID=2, LANGUAGE_CODE='en'):
            with self.login_user_context(superuser):
                # url uses "en" as the request language
                # but the site is configured to use "de" and "fr"
                response = self.client.get('/en/')
                self.assertRedirects(response, '/de/')
                response = self.client.get('/en/%s/' % page_2.get_path('de'))
                self.assertEqual(response.status_code, 404)

    def test_language_fallback(self):
        """
        Test language fallbacks in details view
        """
        from cms.views import details
        p1 = create_page("page", "nav_playground.html", "en", published=True)
        p1.set_as_homepage()

        # There's no "de" translation.
        # Fallbacks are configured.
        # The cms is set to redirect on fallback.
        request = self.get_request('/de/', 'de')
        response = details(request, p1.get_path())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/')

        # There's no "de" translation.
        # There's no fallbacks configured.
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['fallbacks'] = []
        lang_settings[1][1]['fallbacks'] = []

        with self.settings(CMS_LANGUAGES=lang_settings):
            response = self.client.get("/de/")
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
            self.assertRedirects(response, '/en/')

    def test_publish_status(self):
        p1 = create_page("page", "nav_playground.html", "en", published=True)
        public = p1.get_public_object()
        draft = p1.get_draft_object()
        self.assertEqual(set(public.get_languages()), set(('en',)))
        self.assertEqual(set(public.get_published_languages()), set(('en',)))
        self.assertEqual(set(draft.get_languages()), set(('en',)))
        self.assertEqual(set(draft.get_published_languages()), set(('en',)))

        p1 = create_title('de', 'page de', p1).page
        public = p1.get_public_object()
        draft = p1.get_draft_object()
        self.assertEqual(set(public.get_languages()), set(('en',)))
        self.assertEqual(set(public.get_published_languages()), set(('en',)))
        self.assertEqual(set(draft.get_languages()), set(('en', 'de')))
        self.assertEqual(set(draft.get_published_languages()), set(('en', 'de')))

        p1.publish('de')
        p1 = p1.reload()
        public = p1.get_public_object()
        draft = p1.get_draft_object()
        self.assertEqual(set(public.get_languages()), set(('en', 'de')))
        self.assertEqual(set(public.get_published_languages()), set(('en', 'de')))
        self.assertEqual(set(draft.get_languages()), set(('en', 'de')))
        self.assertEqual(set(draft.get_published_languages()), set(('en', 'de')))

        p1.unpublish('de')
        p1 = p1.reload()

        public = p1.get_public_object()
        draft = p1.get_draft_object()
        self.assertEqual(set(public.get_languages()), set(('en', 'de')))
        self.assertEqual(set(public.get_published_languages()), set(('en',)))
        self.assertEqual(set(draft.get_languages()), set(('en', 'de')))
        self.assertEqual(set(draft.get_published_languages()), set(('en', 'de')))

        p1.publish('de')
        p1 = p1.reload()
        p1.unpublish('en')
        p1 = p1.reload()

        public = p1.get_public_object()
        draft = p1.get_draft_object()
        self.assertEqual(set(public.get_languages()), set(('en', 'de')))
        self.assertEqual(set(public.get_published_languages()), set(('de',)))
        self.assertEqual(set(draft.get_languages()), set(('en', 'de')))
        self.assertEqual(set(draft.get_published_languages()), set(('en', 'de')))

    def test_no_english_defined(self):
        with self.settings(TEMPLATE_CONTEXT_PROCESSORS=[],
            CMS_LANGUAGES={
                1:[
                    {'code': 'de', 'name': 'German', 'public':True, 'fallbacks': []},
                ]},
            ):
            try:
                update_site_and_page_choices(language='en-us')
            except LanguageError:
                self.fail("LanguageError raised")

    def test_wrong_plugin_language(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        ph_en = page.placeholders.get(slot="body")
        add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        title = Title(title="page", slug="page", language="ru", page=page)
        title.save()
        # add wrong plugin language
        add_plugin(ph_en, "TextPlugin", "ru", body="I'm the second")
        page.publish('en')
        endpoint = page.get_absolute_url() + '?' + get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
