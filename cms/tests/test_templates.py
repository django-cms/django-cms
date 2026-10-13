import os.path
from importlib.machinery import ModuleSpec
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist, loader
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from cms import constants
from cms.test_utils.testcases import CMSTestCase
from cms.utils.conf import _load_from_file, get_cms_setting

PATH_PREFIX = os.path.join("inner_dir", "custom_templates")
GOOD_PATH = os.path.join(settings.PROJECT_PATH, "project", "templates", PATH_PREFIX)
BAD_PATH = os.path.join(settings.PROJECT_PATH, "project", "custom_templates")
SITE_PATH = {
    1: os.path.join(settings.PROJECT_PATH, "project", "templates", PATH_PREFIX),
    2: os.path.join(settings.PROJECT_PATH, "project", "templates", "%s_2" % PATH_PREFIX),
}


class LoadFromFileTests(SimpleTestCase):
    def test_empty_path_returns_none(self):
        for module_path in (None, ""):
            with self.subTest(module_path=module_path):
                self.assertIsNone(_load_from_file(module_path))

    def test_unsupported_file_type_raises_import_error(self):
        module_path = os.path.join(GOOD_PATH, "base.html")
        with self.assertRaisesMessage(ImportError, f"Cannot load template config: {module_path}"):
            _load_from_file(module_path)

    def test_spec_without_loader_raises_import_error(self):
        module_path = os.path.join(GOOD_PATH, "__init__.py")
        spec = ModuleSpec("mod", loader=None)
        with patch("importlib.util.spec_from_file_location", return_value=spec):
            with self.assertRaisesMessage(ImportError, f"Cannot load template config: {module_path}"):
                _load_from_file(module_path)


class TemplatesConfig(CMSTestCase):
    def test_templates(self):
        """
        Tests that the plain CMS_TEMPLATES works as usual
        """
        original_files = [template[0] for template in settings.CMS_TEMPLATES]
        files = [template[0] for template in get_cms_setting("TEMPLATES")]
        if get_cms_setting("TEMPLATE_INHERITANCE"):
            original_files.append(constants.TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(len(files), 6)
        self.assertEqual(set(files), set(original_files))

    @override_settings(CMS_TEMPLATES_DIR=GOOD_PATH)
    def test_custom_templates(self):
        """Load template names and labels from the configured directory."""
        config_path = os.path.join(settings.CMS_TEMPLATES_DIR, "__init__.py")
        mod = _load_from_file(config_path)
        self.assertIsNotNone(mod)

        original_labels = [force_str(_(template[1])) for template in mod.TEMPLATES.items()]
        original_files = [os.path.join(PATH_PREFIX, template[0].strip()) for template in mod.TEMPLATES.items()]
        templates = get_cms_setting("TEMPLATES")
        self.assertEqual(len(templates), 3)
        labels = [force_str(template[1]) for template in templates]
        files = [template[0] for template in templates]
        if get_cms_setting("TEMPLATE_INHERITANCE"):
            original_labels.append(force_str(_("Inherit the template of the nearest ancestor")))
            original_files.append(constants.TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(set(labels), set(original_labels))
        self.assertEqual(set(files), set(original_files))

    @override_settings(CMS_TEMPLATES_DIR=GOOD_PATH)
    def test_custom_templates_loading(self):
        """
        Checking that templates can be loaded by the template loader
        """
        templates = get_cms_setting("TEMPLATES")
        for template in templates:
            if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                tpl = loader.get_template(template[0])
                self.assertEqual(tpl.template.name, template[0])

    @override_settings(CMS_TEMPLATES_DIR=SITE_PATH)
    def test_multisite(self):
        """
        Checking that templates can be loaded by the template loader
        """
        templates = get_cms_setting("TEMPLATES")
        for template in templates:
            if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                self.assertTrue(template[0].find("%s/" % SITE_PATH[1]) >= -1)
        with self.settings(SITE_ID=2):
            templates = get_cms_setting("TEMPLATES")
            for template in templates:
                if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                    self.assertTrue(template[0].find("%s/" % SITE_PATH[2]) >= -1)

    @override_settings(CMS_TEMPLATES_DIR=BAD_PATH)
    def test_custom_templates_bad_dir(self):
        """
        Checking that templates can be loaded by the template loader
        """
        templates = get_cms_setting("TEMPLATES")
        for template in templates:
            if template[0] != constants.TEMPLATE_INHERITANCE_MAGIC:
                with self.assertRaises(TemplateDoesNotExist):
                    loader.get_template(template[0])

    def test_accepts_custom_django_template_backend(self):
        """
        Test that django CMS accepts template engines that inherit from DjangoTemplates
        """
        custom_templates_settings = [
            {
                "BACKEND": "cms.test_utils.project.template_backends.CustomDjangoTemplates",
                "DIRS": [],
                "OPTIONS": {
                    "context_processors": ["django.template.context_processors.request"],
                },
            }
        ]

        with override_settings(TEMPLATES=custom_templates_settings):
            from cms.utils.setup import validate_settings

            validate_settings()

    def test_rejects_non_django_template_backend(self):
        """
        Test that django CMS rejects template engines that don't inherit from DjangoTemplates
        """
        non_django_templates_settings = [
            {
                "BACKEND": "cms.test_utils.project.template_backends.NonDjangoTemplates",
                "DIRS": [],
                "OPTIONS": {
                    "context_processors": ["django.template.context_processors.request"],
                },
            }
        ]

        with override_settings(TEMPLATES=non_django_templates_settings):
            from cms.utils.setup import validate_settings

            with self.assertRaises(ImproperlyConfigured) as context:
                validate_settings()

            self.assertIn(
                "django.template.backends.django.DjangoTemplates",
                str(context.exception),
                "Should reject non-Django template backends",
            )
