from cms import api
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils import i18n
from django.utils.importlib import import_module
from cms.utils.i18n import get_fallback_languages


class TestLanguages(SettingsOverrideTestCase):

    settings_overrides = {
        'LANGUAGE_CODE': 'en',
        'LANGUAGES': (('fr', 'French'),
                      ('en', 'English'),
                      ('de', 'German'),
                      ('es', 'Spanish')),
        'CMS_LANGUAGES': {
            1: [ {'code' : 'en',
                  'name': 'English',
                  'public': True},
                 {'code': 'fr',
                  'name': 'French',
                  'public': False},
            ],
            'default': {
                'public': True,
                'hide_untranslated': False,
            }
        },
        'SITE_ID': 1,
    }
    
    def test_language_code(self):
        self.assertEqual(i18n.get_language_code(self.settings_overrides['LANGUAGE_CODE']), 'en')
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


class TestLanguagesNoDefault(SettingsOverrideTestCase):

    settings_overrides = {
        'LANGUAGE_CODE': 'en',
        'LANGUAGES': (('fr', 'French'),
                      ('en', 'English'),
                      ('de', 'German'),
                      ('es', 'Spanish')),
        'CMS_LANGUAGES': {
            1: [ {'code' : 'en',
                  'name': 'English',
                  'public': True},
                 {'code': 'fr',
                  'name': 'French',
                  'public': False},
                 ],
        },
        'SITE_ID': 1,
        }

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

            
class TestLanguageCodesEnUS(SettingsOverrideTestCase):

    settings_overrides = {
        'LANGUAGE_CODE': 'en-us',
        'LANGUAGES': (('fr-ca', 'French (Canada)'),
                      ('en-us', 'English (US)'),
                      ('en-gb', 'English (UK)'),
                      ('de', 'German'),
                      ('es', 'Spanish')),
        'CMS_LANGUAGES': {
            1: [ {'code' : 'en-us',
                  'name': 'English (US)',
                  'public': True},
                 {'code': 'fr-ca',
                  'name': 'French (Canada)',
                  'public': False},
            ],
            'default': {
                'public': True,
                'hide_untranslated': False,
            }
        },
        'SITE_ID': 1,
    }
    
    def test_language_code(self):
        self.assertEqual(i18n.get_language_code(self.settings_overrides['LANGUAGE_CODE']), 'en-us')
        self.assertEqual(i18n.get_current_language(), 'en-us') #error
        
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


class TestLanguageCodesEnGB(SettingsOverrideTestCase):

    settings_overrides = {
        'LANGUAGE_CODE': 'en-gb',
        'LANGUAGES': (('fr-ca', 'French (Canada)'),
                      ('en-us', 'English (US)'),
                      ('en-gb', 'English (UK)'),
                      ('de', 'German'),
                      ('es', 'Spanish')),
        'CMS_LANGUAGES': {
            1: [ {'code' : 'en-gb',
                  'name': 'English (UK)',
                  'public': True},
                 {'code': 'fr-ca',
                  'name': 'French (Canada)',
                  'public': False},
            ],
            'default': {
                'public': True,
                'hide_untranslated': False,
            }
        },
        'SITE_ID': 1,
    }
    
    def test_language_code(self):
        self.assertEqual(i18n.get_language_code(self.settings_overrides['LANGUAGE_CODE']), 'en-gb')
        self.assertEqual(i18n.get_current_language(), 'en-gb') #error
        
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


class TestLanguagesNotInCMSLanguages(SettingsOverrideTestCase):
    settings_overrides = {
        'LANGUAGE_CODE': 'en',
        'LANGUAGES': [
            ('en', 'English'),
            ('de', 'German'),
            ('fr', 'French')
        ],
        'CMS_LANGUAGES': {
            1: [
                {
                    'code': 'de',
                    'name': 'German',
                    'public': True,
                },
                {
                    'code': 'fr',
                    'name': 'French',
                    'public': True
                }
            ],
            'default': {
                'fallbacks': ['de', 'fr'],
            }
        },
        'SITE_ID': 1,
    }

    def test_get_fallback_languages(self):
        languages = get_fallback_languages('en', 1)
        self.assertEqual(languages, ['de', 'fr'])


class TestLanguageFallbacks(SettingsOverrideTestCase):

    settings_overrides = {
        'LANGUAGE_CODE': 'en',
        'LANGUAGES': (('fr', 'French'),
                      ('en', 'English'),
                      ('de', 'German'),
                      ('es', 'Spanish')),
        'CMS_LANGUAGES': {
            1: [ {'code' : 'en',
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
        'SITE_ID': 1,
    }

    def test_language_code(self):
        api.create_page("home", "nav_playground.html", "fr", published=True)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/fr/')

    def test_session_language(self):
        with SettingsOverride(CMS_LANGUAGES={
            1: [ {'code' : 'en',
                  'name': 'English',
                  'public': True},
                 {'code': 'fr',
                  'name': 'French',
                  'public': True},
                 ]}):
            page = api.create_page("home", "nav_playground.html", "en", published=True)
            api.create_title('fr', "home", page)
            page.publish('fr')
            page.publish('en')
            response = self.client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/en/')
            from django.conf import settings
            engine = import_module(settings.SESSION_ENGINE)
            store = engine.SessionStore()
            store.save()  # we need to make load() work, or the cookie is worthless
            self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

            #   ugly and long set of session
            session = self.client.session
            session['django_language'] = 'fr'
            session.save()
            response = self.client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/fr/')
            self.client.get('/en/')
            self.assertEqual(self.client.session['django_language'], 'en')
            response = self.client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, '/en/')
