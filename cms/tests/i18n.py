from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.utils import i18n

class TestLanguages(SettingsOverrideTestCase):

    settings_overrides = {
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

    def test_get_languages_default_site(self):
        result = i18n.get_languages()
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_defined_site(self):
        result = i18n.get_languages(1)
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_undefined_site(self):
        result = i18n.get_languages(66)
        self.assertEqual(4, len(result))
        self.assertEqual(result[0]['code'], 'fr')
        self.assertEqual(result[1]['code'], 'en')
        self.assertEqual(result[2]['code'], 'de')
        self.assertEqual(result[3]['code'], 'es')
        for lang in result:
            self.assertEqual(lang['public'], True)
            self.assertEqual(lang['hide_untranslated'], False)


class TestLanguagesNoDefault(SettingsOverrideTestCase):

    settings_overrides = {
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
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_defined_site(self):
        result = i18n.get_languages(1)
        self.assertEqual(2, len(result))
        lang = result[0]
        self.assertEqual(lang['code'], 'en')
        self.assertEqual(lang['public'], True)
        lang = result[1]
        self.assertEqual(lang['code'], 'fr')
        self.assertEqual(lang['public'], False)

    def test_get_languages_undefined_site(self):
        result = i18n.get_languages(66)
        self.assertEqual(4, len(result))
        self.assertEqual(result[0]['code'], 'fr')
        self.assertEqual(result[1]['code'], 'en')
        self.assertEqual(result[2]['code'], 'de')
        self.assertEqual(result[3]['code'], 'es')
        for lang in result:
            self.assertEqual(lang['public'], True)
            self.assertEqual(lang['hide_untranslated'], True)
