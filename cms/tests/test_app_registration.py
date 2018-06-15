import sys
from mock import patch, Mock

from django.test import override_settings
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from cms import app_registration
from cms.test_utils.testcases import CMSTestCase


class AutodiscoverTestCase(CMSTestCase):

    def _clear_autodiscover_imports(self):
        """Helper method to clear imports"""
        sys.path_importer_cache.clear()

        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_extension.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_extension', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_extension.cms_apps', None)

    def setUp(self):
        self._clear_autodiscover_imports()

    def tearDown(self):
        self._clear_autodiscover_imports()

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_cms_extension',
        'cms.tests.test_app_registry.app_without_cms_file'
    ])
    def test_imports_cms_apps_files(self):
        app_registration.autodiscover_cms_files()

        loaded = set([
            str(module) for module in sys.modules
            if 'cms.tests.test_app_registry' in module])
        expected = set([
            'cms.tests.test_app_registry.app_without_cms_file',
            'cms.tests.test_app_registry',
            'cms.tests.test_app_registry.app_with_cms_extension.models',
            'cms.tests.test_app_registry.app_without_cms_file.models',
            'cms.tests.test_app_registry.app_with_cms_extension',
            'cms.tests.test_app_registry.app_with_cms_extension.cms_apps'
        ])
        self.assertSetEqual(loaded, expected)

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_bad_cms_file',
    ])
    def test_raises_exception_raised_in_cms_file(self):
        with self.assertRaises(KeyError):
            app_registration.autodiscover_cms_files()

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_cms_extension',
        'cms.tests.test_app_registry.app_without_cms_file'
    ])
    def test_adds_cms_app_attribute_to_django_app_config(self):
        app_registration.autodiscover_cms_files()

        app_list = [app for app in apps.get_app_configs()]
        self.assertTrue(hasattr(app_list[0], 'cms_app'))
        self.assertEqual(
            app_list[0].cms_app.__class__.__name__, 'CMSSomeFeatureConfig')
        self.assertFalse(hasattr(app_list[1], 'cms_app'))

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_without_cms_app_class',
    ])
    def test_raises_exception_when_no_cms_app_class_found_in_cms_file(self):
        with self.assertRaises(ImproperlyConfigured):
            app_registration.autodiscover_cms_files()

    @override_settings(INSTALLED_APPS=[
        'cms.tests.test_app_registry.app_with_two_cms_app_classes',
    ])
    def test_raises_exception_when_more_than_one_cms_app_class_found_in_cms_file(self):
        with self.assertRaises(ImproperlyConfigured):
            app_registration.autodiscover_cms_files()


class RegisterExtensionsTestCase(CMSTestCase):

    @patch.object(apps, 'get_app_configs')
    def test_runs_register_extension_method_on_cms_app_classes_that_have_it(
        self, mocked_apps
    ):
        # apps with cms_app attr and an extension method
        app_with_cms_ext1 = Mock()
        app_with_cms_ext2 = Mock()
        # app with cms_app attr without an extension method
        # this throws an AttributeError if register_extension is accessed
        app_with_cms_config = Mock(cms_app=Mock(spec=[]))
        # app without cms_app attr
        # this throws an AttributeError if cms_app is accessed
        non_cms_app = Mock(spec=[])
        # mock what apps have been installed
        mocked_apps.return_value = [
            app_with_cms_ext1,
            app_with_cms_config,
            app_with_cms_ext2,
            non_cms_app,
        ]

        app_registration.register_cms_extensions()

        self.assertEqual(
            app_with_cms_ext1.cms_app.register_extension.call_count, 1)
        self.assertEqual(
            app_with_cms_ext2.cms_app.register_extension.call_count, 1)
