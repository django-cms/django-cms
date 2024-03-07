from collections import deque
from importlib import import_module
from unittest.mock import patch

from django.conf import settings
from django.template.context import Context
from django.test.utils import override_settings

from cms import api
from cms.plugin_rendering import (
    ContentRenderer,
    LegacyRenderer,
    StructureRenderer,
)
from cms.test_utils.testcases import CMSTestCase
from cms.utils import get_language_from_request, i18n
from cms.utils.compat import DJANGO_2_2
from cms.views import details

if DJANGO_2_2:
    from django.utils.translation import LANGUAGE_SESSION_KEY


@override_settings(
    LANGUAGE_CODE='en',
    LANGUAGES=(('fr', 'French'),
               ('en', 'English'),
               ('de', 'German'),
               ('es', 'Spanish')),
    CMS_LANGUAGES={
        1: [
            {'code': 'en',
             'name': 'English',
             'public': True},
            {'code': 'fr',
             'name': 'French',
             'public': False},
        ],
        'default': {
            'public': True,
            'hide_untranslated': False,
        },
    },
    SITE_ID=1,
)
class TestLanguages(CMSTestCase):

    def test_language_code(self):
        self.assertEqual(i18n.get_language_code('en'), 'en')
        self.assertEqual(i18n.get_current_language(), 'en')

    def test_get_languages_default_site(self):
        result = i18n.get_languages()
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_defined_site(self):
        result = i18n.get_languages(1)
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_undefined_site(self):
        result = i18n.get_languages(66)
        self.assertEqual(4, len(result))
        self.assertEqual(result[0]['code'], 'fr')
        self.assertEqual(i18n.get_language_code(result[0]['code']), 'fr')
        self.assertEqual(result[1]['code'], 'en')
        self.assertEqual(i18n.get_language_code(result[1]['code']), 'en')
        self.assertEqual(result[2]['code'], 'de')
        self.assertEqual(i18n.get_language_code(result[2]['code']), 'de')
        self.assertEqual(result[3]['code'], 'es')
        self.assertEqual(i18n.get_language_code(result[3]['code']), 'es')
        for lang in result:
            self.assertEqual(lang['public'], True)
            self.assertEqual(lang['hide_untranslated'], False)


@override_settings(
    LANGUAGE_CODE='en',
    LANGUAGES=(('fr', 'French'),
               ('en', 'English'),
               ('de', 'German'),
               ('es', 'Spanish')),
    CMS_LANGUAGES={
        1: [
            {'code': 'en',
             'name': 'English',
             'public': True},
            {'code': 'fr',
             'name': 'French',
             'public': False},
        ],
    },
    SITE_ID=1,
)
class TestLanguagesNoDefault(CMSTestCase):

    def test_get_languages_default_site(self):
        result = i18n.get_languages()
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_defined_site(self):
        result = i18n.get_languages(1)
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_undefined_site(self):
        result = i18n.get_languages(66)
        self.assertEqual(4, len(result))
        self.assertEqual(result[0]['code'], 'fr')
        self.assertEqual(i18n.get_language_code(result[0]['code']), 'fr')
        self.assertEqual(result[1]['code'], 'en')
        self.assertEqual(i18n.get_language_code(result[1]['code']), 'en')
        self.assertEqual(result[2]['code'], 'de')
        self.assertEqual(i18n.get_language_code(result[2]['code']), 'de')
        self.assertEqual(result[3]['code'], 'es')
        self.assertEqual(i18n.get_language_code(result[3]['code']), 'es')
        for lang in result:
            self.assertEqual(lang['public'], True)
            self.assertEqual(lang['hide_untranslated'], True)


@override_settings(
    LANGUAGE_CODE='en-us',
    LANGUAGES=(('fr-ca', 'French (Canada)'),
               ('en-us', 'English (US)'),
               ('en-gb', 'English (UK)'),
               ('de', 'German'),
               ('es', 'Spanish')),
    CMS_LANGUAGES={
        1: [
            {'code': 'en-us',
             'name': 'English (US)',
             'public': True},
            {'code': 'fr-ca',
             'name': 'French (Canada)',
             'public': False},
        ],
        'default': {
            'public': True,
            'hide_untranslated': False,
        },
    },
    SITE_ID=1,
)
class TestLanguageCodesEnUS(CMSTestCase):

    def test_language_code(self):
        self.assertEqual(i18n.get_language_code('en-us'), 'en-us')
        self.assertEqual(i18n.get_current_language(), 'en-us')

    def test_get_languages_default_site(self):
        result = i18n.get_languages()
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en-us')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en-us')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr-ca')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr-ca')
        self.assertEqual(lang['public'], False)

    def test_get_languages_defined_site(self):
        result = i18n.get_languages(1)
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en-us')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en-us')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr-ca')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr-ca')
        self.assertEqual(lang['public'], False)

    def test_get_languages_undefined_site(self):
        result = i18n.get_languages(66)
        self.assertEqual(5, len(result))
        self.assertEqual(result[0]['code'], 'fr-ca')
        self.assertEqual(i18n.get_language_code(result[0]['code']), 'fr-ca')
        self.assertEqual(result[1]['code'], 'en-us')
        self.assertEqual(i18n.get_language_code(result[1]['code']), 'en-us')
        self.assertEqual(result[2]['code'], 'en-gb')
        self.assertEqual(i18n.get_language_code(result[2]['code']), 'en-gb')
        self.assertEqual(result[3]['code'], 'de')
        self.assertEqual(i18n.get_language_code(result[3]['code']), 'de')
        self.assertEqual(result[4]['code'], 'es')
        self.assertEqual(i18n.get_language_code(result[4]['code']), 'es')
        for lang in result:
            self.assertEqual(lang['public'], True)
            self.assertEqual(lang['hide_untranslated'], False)


@override_settings(
    LANGUAGE_CODE='en-gb',
    LANGUAGES=(('fr-ca', 'French (Canada)'),
               ('en-us', 'English (US)'),
               ('en-gb', 'English (UK)'),
               ('de', 'German'),
               ('es', 'Spanish')),
    CMS_LANGUAGES={
        1: [
            {'code': 'en-gb',
             'name': 'English (UK)',
             'public': True},
            {'code': 'fr-ca',
             'name': 'French (Canada)',
             'public': False},
        ],
        'default': {
            'public': True,
            'hide_untranslated': False,
        },
    },
    SITE_ID=1,
)
class TestLanguageCodesEnGB(CMSTestCase):

    def test_language_code(self):
        self.assertEqual(i18n.get_language_code('en-gb'), 'en-gb')
        self.assertEqual(i18n.get_current_language(), 'en-gb')

    def test_get_languages_default_site(self):
        result = i18n.get_languages()
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en-gb')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en-gb')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr-ca')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr-ca')
        self.assertEqual(lang['public'], False)

    def test_get_languages_defined_site(self):
        result = i18n.get_languages(1)
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en-gb')
        self.assertEqual(i18n.get_language_code(lang['code']), 'en-gb')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr-ca')
        self.assertEqual(i18n.get_language_code(lang['code']), 'fr-ca')
        self.assertEqual(lang['public'], False)

    def test_get_languages_undefined_site(self):
        result = i18n.get_languages(66)
        self.assertEqual(5, len(result))
        self.assertEqual(result[0]['code'], 'fr-ca')
        self.assertEqual(i18n.get_language_code(result[0]['code']), 'fr-ca')
        self.assertEqual(result[1]['code'], 'en-us')
        self.assertEqual(i18n.get_language_code(result[1]['code']), 'en-us')
        self.assertEqual(result[2]['code'], 'en-gb')
        self.assertEqual(i18n.get_language_code(result[2]['code']), 'en-gb')
        self.assertEqual(result[3]['code'], 'de')
        self.assertEqual(i18n.get_language_code(result[3]['code']), 'de')
        self.assertEqual(result[4]['code'], 'es')
        self.assertEqual(i18n.get_language_code(result[4]['code']), 'es')
        for lang in result:
            self.assertEqual(lang['public'], True)
            self.assertEqual(lang['hide_untranslated'], False)


@override_settings(
    LANGUAGE_CODE='en',
    LANGUAGES=[
        ('en', 'English'),
        ('de', 'German'),
        ('fr', 'French')
    ],
    CMS_LANGUAGES={
        1: [{'code': 'de',
             'name': 'German',
             'public': True},
            {'code': 'fr',
             'name': 'French',
             'public': True}],
        'default': {
            'fallbacks': ['de', 'fr'],
        },
    },
    SITE_ID=1,
)
class TestLanguagesNotInCMSLanguages(CMSTestCase):

    def test_get_fallback_languages(self):
        languages = i18n.get_fallback_languages('en', 1)
        self.assertEqual(languages, ['de', 'fr'])


@override_settings(
    LANGUAGE_CODE='en',
    LANGUAGES=(('fr', 'French'),
               ('en', 'English'),
               ('de', 'German'),
               ('es', 'Spanish')),
    CMS_LANGUAGES={
        1: [
            {'code': 'en',
             'name': 'English',
             'public': False},
            {'code': 'fr',
             'name': 'French',
             'public': True},
        ],
        'default': {
            'fallbacks': ['en', 'fr'],
            'redirect_on_fallback': False,
            'public': True,
            'hide_untranslated': False,
        }
    },
    SITE_ID=1,
)
class TestLanguageFallbacks(CMSTestCase):

    def test_language_code(self):
        '''
        No redirect_on_fallback will return 200 with the fallback content
        '''
        self.create_homepage("home", "nav_playground.html", "fr")
        response = self.client.get('/')
        # no language code will cause a redirect.
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/fr/')
        self.assertEqual(response.status_code, 200)

    @override_settings(
        CMS_LANGUAGES={
            1: [
                {'code': 'en',
                 'name': 'English',
                 'public': True},
                {'code': 'fr',
                 'name': 'French',
                 'public': True},
            ]
        },
    )
    def test_session_language(self):
        page = self.create_homepage("home", "nav_playground.html", "en")
        api.create_page_content('fr', "home", page)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/')
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

        #   ugly and long set of session
        session = self.client.session
        if not DJANGO_2_2:
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'fr'
        else:
            session[LANGUAGE_SESSION_KEY] = 'fr'
            session.save()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/fr/')
        self.client.get('/en/')
        if not DJANGO_2_2:
            self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, 'en')
        else:
            self.assertEqual(self.client.session[LANGUAGE_SESSION_KEY], 'en')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/en/')

    @override_settings(
        CMS_LANGUAGES={
            'default': {
                'fallbacks': ['en', 'fr'],
                'public': True,  # no 404s
                'redirect_on_fallback': False
            }
        },
    )
    def test_no_redirect_on_fallback(self):
        homepage = self.create_homepage(
            "home",
            "nav_playground.html",
            "fr"
        )
        page_data = self.get_new_page_data_dbfields(
            language="fr"
        )
        page = api.create_page(**page_data)
        response = self.client.get(page.get_absolute_url(language="en"))
        self.assertEqual(response.status_code, 200)

        # homepage should be the same
        response = self.client.get(homepage.get_absolute_url(language="en"))
        self.assertEqual(response.status_code, 200)

    @override_settings(
        CMS_LANGUAGES={
            'default': {
                'fallbacks': ['en', 'fr'],
                'public': True,  # no 404s
                'redirect_on_fallback': False
            }
        },
    )
    def test_no_redirect_on_fallback_content(self):
        """
        Test that the fallback content will be displayed
        """
        homepage = self.create_homepage(
            "home",
            "nav_playground.html",
            "fr"
        )
        homepage_ph_fr = homepage.get_placeholders(
            "fr").get(slot="body")
        api.add_plugin(
            homepage_ph_fr,
            plugin_type="TextPlugin",
            language="fr",
            body="Hello, world!",
        )
        page_data = self.get_new_page_data_dbfields(
            language="fr"
        )
        page = api.create_page(**page_data)
        page_ph_fr = page.get_placeholders(
            "fr").get(slot="body")
        api.add_plugin(
            page_ph_fr,
            plugin_type="TextPlugin",
            language="fr",
            body="Hello, world!",
        )
        with patch("cms.views.render_pagecontent") as mock_render:
            # normal page
            path = page.get_absolute_url(language="en")
            request = self.get_request(path)
            details(request, slug=page.get_path("en"))
            mock_render.assert_called_once_with(
                request,
                page.get_content_obj()
            )
            # check that the french plugins will render
            context = Context({'request': request})
            rendered_placeholder = self._render_placeholder(page_ph_fr, context)
            self.assertEqual(rendered_placeholder, "Hello, world!")

        with patch("cms.views.render_pagecontent") as mock_render:
            # homepage should be the same
            path = homepage.get_absolute_url(language="en")
            request = self.get_request(path)
            details(request, slug=homepage.get_path("en"))
            mock_render.assert_called_once_with(
                request,
                homepage.get_content_obj()
            )
            # check that the french plugins will render
            context = Context({'request': request})
            rendered_placeholder = self._render_placeholder(homepage_ph_fr, context)
            self.assertEqual(rendered_placeholder, "Hello, world!")

    @override_settings(
        CMS_LANGUAGES={
            'default': {
                'fallbacks': ['en', 'fr'],
                'redirect_on_fallback': True,
            }
        }
    )
    def test_redirect_on_fallback(self):
        page_data = self.get_new_page_data_dbfields(
            language="fr"
        )
        page = api.create_page(**page_data)
        response_fr = self.client.get(page.get_absolute_url(language="fr"))
        self.assertEqual(response_fr.status_code, 200)
        response_en = self.client.get(page.get_absolute_url(language="en"))
        self.assertRedirects(response_en, page.get_absolute_url(language="fr"))

        # homepage should be no different.
        home_page_data = self.get_new_page_data_dbfields(
            language="fr",
        )
        self.create_homepage(**home_page_data)
        response_fr = self.client.get(page.get_absolute_url(language="fr"))
        self.assertEqual(response_fr.status_code, 200)
        response_en = self.client.get(page.get_absolute_url(language="en"))
        self.assertRedirects(response_en, page.get_absolute_url(language="fr"))

@override_settings(
    LANGUAGE_CODE='en',
    LANGUAGES=(('fr', 'French'),
               ('en', 'English'),
               ('de', 'German'),
               ('es', 'Spanish')),
    CMS_LANGUAGES={
        1: [
            {'code': 'en',
             'name': 'English',
             'public': False},
            {'code': 'fr',
             'name': 'French',
             'public': True},
        ],
        'default': {
            'fallbacks': ['en', 'fr'],
            'redirect_on_fallback': False,
            'public': True,
            'hide_untranslated': False,
        }
    },
    SITE_ID=1,
)
class TestGetLanguageFromRequest(CMSTestCase):

    def test_get_language_from_request_does_not_return_empty_string_from_post(self):
        request = self.get_request(language='en', post_data={
            'language': '',
        })
        self.assertEqual(get_language_from_request(request), 'en')

    def test_get_language_from_request_does_not_return_empty_string_from_get(self):
        request = self.get_request('/en/?language=', language='en')
        self.assertEqual(get_language_from_request(request), 'en')
