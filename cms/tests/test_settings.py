from classytags.utils import flatten_context
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.test.utils import override_settings

from cms import constants
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import get_cms_setting


class SettingsTests(CMSTestCase):
    @override_settings(
        CMS_TEMPLATES=[('subdir/template.html', 'Subdir')],
        DEBUG=True,
        TEMPLATE_DEBUG=True,
    )
    def test_cms_templates_with_pathsep(self):
        from sekizai.context import SekizaiContext
        context = flatten_context(SekizaiContext())
        self.assertEqual(render_to_string('subdir/template.html', context).strip(), 'test')

    @override_settings(SITE_ID='broken')
    def test_non_numeric_site_id(self):
        self.assertRaises(
            ImproperlyConfigured,
            get_cms_setting, 'LANGUAGES'
        )

    @override_settings(LANGUAGE_CODE='en-us')
    def test_invalid_language_code(self):
        self.assertRaises(
            ImproperlyConfigured,
            get_cms_setting, 'LANGUAGES'
        )

    @override_settings(CMS_TEMPLATE_INHERITANCE=True)
    def test_create_page_with_inheritance_override(self):
        for template in get_cms_setting('TEMPLATES'):
            if (template[0] == constants.TEMPLATE_INHERITANCE_MAGIC):
                return
        self.assertRaises(
            ImproperlyConfigured,
            get_cms_setting, 'TEMPLATES'
        )

    @override_settings(CMS_TEMPLATE_INHERITANCE=False)
    def test_create_page_without_inheritance_override(self):
        for template in get_cms_setting('TEMPLATES'):
            if (template[0] == constants.TEMPLATE_INHERITANCE_MAGIC):
                self.assertRaises(
                    ImproperlyConfigured,
                    get_cms_setting, 'TEMPLATES'
                )
