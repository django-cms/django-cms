# -*- coding: utf-8 -*-
from imp import load_module, PY_SOURCE
import os.path

from django.conf import settings
from django.template import loader, TemplateDoesNotExist
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from cms import constants
from cms.test_utils.testcases import CMSTestCase
from cms.utils import get_cms_setting

PATH_PREFIX = os.path.join('inner_dir', 'custom_templates')
GOOD_PATH = os.path.join(settings.PROJECT_PATH, 'project', 'templates', PATH_PREFIX)
BAD_PATH = os.path.join(settings.PROJECT_PATH, 'project', 'custom_templates')
SITE_PATH = {
    1: os.path.join(settings.PROJECT_PATH, 'project', 'templates', PATH_PREFIX),
    2: os.path.join(settings.PROJECT_PATH, 'project', 'templates', '%s_2' % PATH_PREFIX),
}


class TemplatesConfig(CMSTestCase):

    def test_templates(self):
        """
        Tests that the plain CMS_TEMPLATES works as usual
        """
        original_files = [template[0] for template in settings.CMS_TEMPLATES]
        files = [template[0] for template in get_cms_setting('TEMPLATES')]
        if get_cms_setting('TEMPLATE_INHERITANCE'):
            original_files.append(constants.TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(len(files), 6)
        self.assertEqual(set(files), set(original_files))

    @override_settings(CMS_TEMPLATES_DIR=GOOD_PATH)
    def test_custom_templates(self):
        """
        Test that using CMS_TEMPLATES_DIR both template list and template labels are extracted from the new directory
        """
        config_path = os.path.join(settings.CMS_TEMPLATES_DIR, '__init__.py')
        with open(config_path, 'r') as openfile:
            mod = load_module("mod", openfile, config_path, ('m', 'r', PY_SOURCE))
        original_labels = [force_text(_(template[1])) for template in mod.TEMPLATES.items()]
        original_files = [os.path.join(PATH_PREFIX, template[0].strip()) for template in mod.TEMPLATES.items()]
        templates = get_cms_setting('TEMPLATES')
        self.assertEqual(len(templates), 3)
        labels = [force_text(template[1]) for template in templates]
        files = [template[0] for template in templates]
        if get_cms_setting('TEMPLATE_INHERITANCE'):
            original_labels.append(force_text(_('Inherit the template of the nearest ancestor')))
            original_files.append(constants.TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(set(labels), set(original_labels))
        self.assertEqual(set(files), set(original_files))

    @override_settings(CMS_TEMPLATES_DIR=GOOD_PATH)
    def test_custom_templates_loading(self):
        """
        Checking that templates can be loaded by the template loader
        """
        templates = get_cms_setting('TEMPLATES')
        for template in templates:
            if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                tpl = loader.get_template(template[0])
                self.assertEqual(tpl.template.name, template[0])

    @override_settings(CMS_TEMPLATES_DIR=SITE_PATH)
    def test_multisite(self):
        """
        Checking that templates can be loaded by the template loader
        """
        templates = get_cms_setting('TEMPLATES')
        for template in templates:
            if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                self.assertTrue(template[0].find('%s/' % SITE_PATH[1]) >= -1)
        with self.settings(SITE_ID=2):
            templates = get_cms_setting('TEMPLATES')
            for template in templates:
                if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                    self.assertTrue(template[0].find('%s/' % SITE_PATH[2]) >= -1)


    @override_settings(CMS_TEMPLATES_DIR=BAD_PATH)
    def test_custom_templates_bad_dir(self):
        """
        Checking that templates can be loaded by the template loader
        """
        templates = get_cms_setting('TEMPLATES')
        for template in templates:
            if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                with self.assertRaises(TemplateDoesNotExist):
                    loader.get_template(template[0])
