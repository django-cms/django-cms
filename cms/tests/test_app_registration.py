import sys

from django.test import override_settings

from cms.test_utils.testcases import CMSTestCase
from cms.app_registration import autodiscover_cms_files


class AutodiscoverTestCase(CMSTestCase):

    def setUp(self):
        sys.path_importer_cache.clear()

        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file.cms_apps', None)

    def tearDown(self):
        sys.path_importer_cache.clear()

        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_without_cms_file.models', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file', None)
        sys.modules.pop('cms.tests.test_app_registry.app_with_cms_file.cms_apps', None)

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
