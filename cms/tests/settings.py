# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms import constants
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string

class SettingsTests(CMSTestCase):
    def test_cms_templates_with_pathsep(self):
        from sekizai.context import SekizaiContext
        with SettingsOverride(CMS_TEMPLATES=[('subdir/template.html', 'Subdir')], DEBUG=True, TEMPLATE_DEBUG=True):
            context = SekizaiContext()
            self.assertEqual(render_to_string('subdir/template.html', context).strip(), 'test')
