# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms import constants
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils import get_cms_setting
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string


class SettingsTests(CMSTestCase):
    def test_cms_templates_with_pathsep(self):
        from sekizai.context import SekizaiContext
        with SettingsOverride(CMS_TEMPLATES=[('subdir/template.html', 'Subdir')], DEBUG=True, TEMPLATE_DEBUG=True):
            context = SekizaiContext()
            self.assertEqual(render_to_string('subdir/template.html', context).strip(), 'test')

    def test_non_numeric_site_id(self):
        with SettingsOverride(SITE_ID='broken'):
            self.assertRaises(
                ImproperlyConfigured,
                get_cms_setting, 'LANGUAGES'
            )

    def test_invalid_language_code(self):
        with SettingsOverride(LANGUAGE_CODE='en-us'):
            self.assertRaises(
                ImproperlyConfigured,
                get_cms_setting, 'LANGUAGES'
            )

    def test_create_page_with_inheritance_override(self):
        with SettingsOverride(CMS_TEMPLATE_INHERITANCE=True):
            for template in get_cms_setting('TEMPLATES'):
                if (template[0] == constants.TEMPLATE_INHERITANCE_MAGIC):
                    return
            self.assertRaises(
                ImproperlyConfigured,
                get_cms_setting, 'TEMPLATES'
            )
    
    def test_create_page_without_inheritance_override(self):
        with SettingsOverride(CMS_TEMPLATE_INHERITANCE=False):
            for template in get_cms_setting('TEMPLATES'):
                if (template[0] == constants.TEMPLATE_INHERITANCE_MAGIC):
                    self.assertRaises(
                        ImproperlyConfigured,
                        get_cms_setting, 'TEMPLATES'
                    )
