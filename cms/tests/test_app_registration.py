import sys

from django.test import override_settings
from django.apps import apps

from cms.test_utils.testcases import CMSTestCase
from cms.app_registration import autodiscover_cms_files


class AutodiscoverTestCase(CMSTestCase):

    def _clear_autodiscover_imports(self):
        """Helper method to clear imports"""
        sys.path_importer_cache.clear()

        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file.cms_apps', None)

    def setUp(self):
        self._clear_autodiscover_imports()

    def tearDown(self):
        self._clear_autodiscover_imports()

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_cms_file',
        'cms.tests.test_app_registry.app_without_cms_file'
    ])
    def test_imports_cms_apps_files(self):
        autodiscover_cms_files()

        loaded = set([
            str(module) for module in sys.modules
            if 'cms.tests.test_app_registry' in module])
        expected = set([
            'cms.tests.test_app_registry.app_without_cms_file',
            'cms.tests.test_app_registry',
            'cms.tests.test_app_registry.app_with_cms_file.models',
            'cms.tests.test_app_registry.app_without_cms_file.models',
            'cms.tests.test_app_registry.app_with_cms_file',
            'cms.tests.test_app_registry.app_with_cms_file.cms_apps'
        ])
        self.assertSetEqual(loaded, expected)

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_bad_cms_file',
    ])
    def test_raises_exception_raised_in_cms_file(self):
        with self.assertRaises(KeyError):
            autodiscover_cms_files()

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_cms_file',
        'cms.tests.test_app_registry.app_without_cms_file'
    ])
    def test_adds_cms_app_class_to_django_app_config(self):
        autodiscover_cms_files()

        app_list = [app for app in apps.get_app_configs()]
        self.assertTrue(hasattr(app_list[0], 'cms_app'))
        self.assertEqual(
            app_list[0].cms_app.__class__.__name__, 'CMSSomeFeatureConfig')
        self.assertFalse(hasattr(app_list[1], 'cms_app'))
