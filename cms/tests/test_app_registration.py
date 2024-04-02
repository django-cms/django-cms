from importlib import import_module
from unittest.mock import Mock, patch

from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from cms import app_registration
from cms.apps import CMSConfig
from cms.test_utils.testcases import CMSTestCase
from cms.utils import setup


class AutodiscoverTestCase(CMSTestCase):

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_cms_config',
    ])
    def test_adds_only_cms_config_attr_to_config_only_app(self):
        app_registration.autodiscover_cms_configs()

        app = apps.get_app_config('app_with_cms_config')
        # Make sure the app has a cms_config attribute
        self.assertTrue(hasattr(app, 'cms_config'))
        self.assertEqual(
            app.cms_config.__class__.__name__, 'CMSConfigConfig')
        self.assertEqual(app.cms_config.app_config, app)
        # Make sure the app doesn't have a cms_extension attribute
        self.assertFalse(hasattr(app, 'cms_extension'))

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_cms_feature_and_config',
    ])
    def test_adds_both_cms_config_and_cms_extension_attr(self):
        app_registration.autodiscover_cms_configs()

        app = apps.get_app_config('app_with_cms_feature_and_config')
        # Make sure the app has a cms_config attribute
        self.assertTrue(hasattr(app, 'cms_config'))
        self.assertEqual(
            app.cms_config.__class__.__name__, 'CMSConfig')
        self.assertEqual(app.cms_config.app_config, app)
        # Make sure the app has a cms_extension attribute
        self.assertTrue(hasattr(app, 'cms_extension'))
        self.assertEqual(
            app.cms_extension.__class__.__name__, 'CMSExtension')

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_without_cms_file',
    ])
    def test_doesnt_add_attrs_to_app_without_cms_config(self):
        app_registration.autodiscover_cms_configs()

        app = apps.get_app_config('app_without_cms_file')
        # Make sure the app doesn't have a cms_config attribute
        self.assertFalse(hasattr(app, 'cms_config'))
        # Make sure the app doesn't have a cms_extension attribute
        self.assertFalse(hasattr(app, 'cms_extension'))

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_bad_cms_file',
    ])
    def test_exception_propagates_from_cms_file(self):
        # The cms file intentionally raises a RuntimeError. We need
        # to make sure the exception definitely bubbles up and doesn't
        # get caught.
        with self.assertRaises(RuntimeError):
            app_registration.autodiscover_cms_configs()

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_without_cms_app_class',
    ])
    def test_raises_exception_when_no_cms_app_class_found_in_cms_file(self):
        # No cms config defined in the cms file so raise exception
        with self.assertRaises(ImproperlyConfigured):
            app_registration.autodiscover_cms_configs()

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_two_cms_config_classes',
    ])
    def test_raises_exception_when_more_than_one_cms_config_class_found_in_cms_file(self):
        # More than one cms config defined so raise exception
        with self.assertRaises(ImproperlyConfigured):
            app_registration.autodiscover_cms_configs()

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_two_cms_feature_classes',
    ])
    def test_raises_exception_when_more_than_one_cms_extension_class_found_in_cms_file(self):
        # More than one cms extension defined so raise exception
        with self.assertRaises(ImproperlyConfigured):
            app_registration.autodiscover_cms_configs()


class GetCmsExtensionAppsTestCase(CMSTestCase):

    def setUp(self):
        # The result of get_cms_extension_apps is cached. Clear this cache
        # because installed apps change between tests and therefore
        # unlike in a live environment, results of this function
        # can change between tests
        app_registration.get_cms_extension_apps.cache_clear()

    @patch.object(apps, 'get_app_configs')
    def test_returns_only_cms_apps_with_extension(self, mocked_apps):
        app_with_extension = Mock(label='a', cms_extension=Mock(), spec=[])
        app_with_config = Mock(label='b', cms_config=Mock(), spec=[])
        app_with_both = Mock(
            label='c', cms_config=Mock(), cms_extension=Mock(), spec=[])
        non_cms_app = Mock(label='d', spec=[]),
        mocked_apps.return_value = [
            app_with_extension,
            app_with_config,
            app_with_both,
            non_cms_app,
        ]

        cms_apps = app_registration.get_cms_extension_apps()

        # Of the 4 installed apps only 2 have extensions
        self.assertListEqual(
            cms_apps, [app_with_extension, app_with_both])


class GetCmsConfigAppsTestCase(CMSTestCase):

    def setUp(self):
        # The result of get_cms_config_apps is cached. Clear this cache
        # because installed apps change between tests and therefore
        # unlike in a live environment, results of this function
        # can change between tests
        app_registration.get_cms_config_apps.cache_clear()

    @patch.object(apps, 'get_app_configs')
    def test_returns_only_cms_apps_with_config(self, mocked_apps):
        app_with_extension = Mock(label='a', cms_extension=Mock(), spec=[])
        app_with_config = Mock(label='b', cms_config=Mock(), spec=[])
        app_with_both = Mock(
            label='c', cms_config=Mock(), cms_extension=Mock(), spec=[])
        non_cms_app = Mock(label='d', spec=[]),
        mocked_apps.return_value = [
            app_with_extension,
            app_with_config,
            app_with_both,
            non_cms_app,
        ]

        cms_apps = app_registration.get_cms_config_apps()

        # Of the 4 installed apps only 2 have configs
        self.assertListEqual(
            cms_apps, [app_with_config, app_with_both])


class ConfigureCmsAppsTestCase(CMSTestCase):

    def setUp(self):
        # The result of get_cms_config_apps is cached. Clear this cache
        # because installed apps change between tests and therefore
        # unlike in a live environment, results of this function
        # can change between tests
        app_registration.get_cms_config_apps.cache_clear()

    @patch.object(apps, 'get_app_configs')
    def test_runs_configure_app_method_for_app_with_enabled_config(self, mocked_apps):
        # Set up app with label djangocms_feature_x that has a cms feature
        feature_app = Mock(spec=AppConfig)
        feature_app.label = 'djangocms_feature_x'
        feature_app.cms_extension = Mock(spec=['configure_app'])
        # Set up app that makes use of djangocms_feature_x
        config_app = Mock(spec=AppConfig)
        config_app.cms_config = Mock(
            spec=['djangocms_feature_x_enabled'])
        config_app.cms_config.djangocms_feature_x_enabled = True
        # Pretend these mocked apps are in INSTALLED_APPS
        mocked_apps.return_value = [
            feature_app, config_app]

        app_registration.configure_cms_apps([feature_app])

        # If an app has enabled a feature, the configure method
        # for that feature should have run with that app as the arg
        feature_app.cms_extension.configure_app.assert_called_once_with(
            config_app.cms_config)

    @patch.object(apps, 'get_app_configs')
    def test_doesnt_run_configure_app_method_for_disabled_app(self, mocked_apps):
        # Set up app with label djangocms_feature_x that has a cms feature
        feature_app = Mock(spec=AppConfig)
        feature_app.label = 'djangocms_feature_x'
        feature_app.cms_extension = Mock(spec=['configure_app'])
        # Set up two apps that do not make use of djangocms_feature_x.
        # One does not define the enabled attr at all (most common
        # use case) and one defines it as False
        config_app_disabled1 = Mock(spec=AppConfig)
        config_app_disabled1.cms_config = Mock(spec=[])
        config_app_disabled2 = Mock(spec=AppConfig)
        config_app_disabled2.cms_config = Mock(
            spec=['djangocms_feature_x_enabled'])
        config_app_disabled2.cms_config.djangocms_feature_x_enabled = False
        # Pretend all these mocked apps are in INSTALLED_APPS
        mocked_apps.return_value = [
            feature_app, config_app_disabled1, config_app_disabled2]

        app_registration.configure_cms_apps([feature_app])

        # If an app has not enabled a feature, the configure method
        # for that feature should not have been run for that app
        self.assertFalse(feature_app.cms_extension.configure_app.called)

    @patch.object(apps, 'get_app_configs')
    def test_doesnt_raise_exception_if_not_cms_app(self, mocked_apps):
        # Set up app with label djangocms_feature_x that has a cms feature
        feature_app = Mock(spec=AppConfig)
        feature_app.label = 'djangocms_feature_x'
        feature_app.cms_extension = Mock(spec=['configure_app'])
        # Set up non cms app
        non_cms_app = Mock(spec=AppConfig)
        # Pretend these mocked apps are in INSTALLED_APPS
        mocked_apps.return_value = [feature_app, non_cms_app]

        # An app that does not define a cms config should just be
        # ignored and not cause any exceptions
        try:
            app_registration.configure_cms_apps([feature_app])
        except AttributeError:
            self.fail("Exception raised when cms app config not defined")

    @patch.object(apps, 'get_app_configs')
    def test_runs_configure_app_method_for_correct_apps_when_multiple_apps(self, mocked_apps):
        # Set up app with label djangocms_feature_x that has a cms feature
        feature_app_x = Mock(spec=AppConfig)
        feature_app_x.label = 'djangocms_feature_x'
        feature_app_x.cms_extension = Mock(spec=['configure_app'])
        # Set up app with label djangocms_feature_y that has a cms feature
        feature_app_y = Mock(spec=AppConfig)
        feature_app_y.label = 'djangocms_feature_y'
        feature_app_y.cms_extension = Mock(spec=['configure_app'])
        # Set up apps that make use of djangocms_feature_x
        config_app_x = Mock(spec=AppConfig)
        config_app_x.cms_config = Mock(
            spec=['djangocms_feature_x_enabled'])
        config_app_x.cms_config.djangocms_feature_x_enabled = True
        # Set up app that makes use of djangocms_feature_y
        config_app_y = Mock(spec=AppConfig)
        config_app_y.cms_config = Mock(
            spec=['djangocms_feature_y_enabled'])
        config_app_y.cms_config.djangocms_feature_y_enabled = True
        # Set up app that makes use of feature x & y
        config_app_xy = Mock(spec=AppConfig)
        config_app_xy.cms_config = Mock(
            spec=['djangocms_feature_x_enabled',
                  'djangocms_feature_y_enabled']
        )
        config_app_xy.cms_config.djangocms_feature_x_enabled = True
        config_app_xy.cms_config.djangocms_feature_y_enabled = True
        # Set up non cms app
        non_cms_app = Mock(spec=AppConfig)
        # Pretend these mocked apps are in INSTALLED_APPS
        mocked_apps.return_value = [
            feature_app_x, non_cms_app, config_app_xy, config_app_y,
            config_app_x, feature_app_y]

        app_registration.configure_cms_apps(
            [feature_app_x, feature_app_y])

        # Assert we configured the 2 apps we expected with feature x
        self.assertEqual(
            feature_app_x.cms_extension.configure_app.call_count, 2)
        self.assertEqual(
            feature_app_x.cms_extension.configure_app.call_args_list[0][0][0],
            config_app_xy.cms_config)
        self.assertEqual(
            feature_app_x.cms_extension.configure_app.call_args_list[1][0][0],
            config_app_x.cms_config)
        # Assert we configured the 2 apps we expected with feature y
        self.assertEqual(
            feature_app_y.cms_extension.configure_app.call_count, 2)
        self.assertEqual(
            feature_app_y.cms_extension.configure_app.call_args_list[0][0][0],
            config_app_xy.cms_config)
        self.assertEqual(
            feature_app_y.cms_extension.configure_app.call_args_list[1][0][0],
            config_app_y.cms_config)

    @patch.object(apps, 'get_app_configs')
    def test_runs_ready_for_all_extensions(self, mocked_apps):
        feature_app = Mock(spec=AppConfig)
        feature_app.label = 'djangocms_feature_x'
        feature_app.cms_extension = Mock(spec=['ready'])

        mocked_apps.return_value = [feature_app]

        app_registration.ready_cms_apps([feature_app])

        feature_app.cms_extension.ready.assert_called_once_with()


class SetupCmsAppsTestCase(CMSTestCase):

    def setUp(self):
        # The results of get_cms_extension_apps and get_cms_config_apps
        # are cached. Clear this cache because installed apps change
        # between tests and therefore unlike in a live environment,
        # results of this function can change between tests
        app_registration.get_cms_extension_apps.cache_clear()
        app_registration.get_cms_config_apps.cache_clear()

    @patch.object(setup, 'setup_cms_apps')
    def test_setup_cms_apps_function_run_on_startup(self, mocked_setup):
        cms_module = import_module('cms')

        CMSConfig('app_name', cms_module).ready()

        mocked_setup.assert_called_once()

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_cms_feature',
        'cms.test_utils.project.app_with_cms_feature_and_config',
        'cms.test_utils.project.app_without_cms_file',
        'cms.test_utils.project.app_with_cms_config'
    ])
    def test_cms_apps_setup_after_setup_function_run(self):
        # This is the function that gets run on startup
        setup.setup_cms_apps()

        # Get the django app configs to do asserts on them later
        feature_app = apps.get_app_config('app_with_cms_feature')
        config_app = apps.get_app_config('app_with_cms_config')
        feature_and_config_app = apps.get_app_config(
            'app_with_cms_feature_and_config')
        non_cms_app = apps.get_app_config('app_without_cms_file')

        # cms_config attribute has been added to all app configs
        # that define a cms config class
        self.assertFalse(hasattr(non_cms_app, 'cms_config'))
        self.assertFalse(hasattr(feature_app, 'cms_config'))
        self.assertTrue(hasattr(config_app, 'cms_config'))
        self.assertTrue(hasattr(feature_and_config_app, 'cms_config'))

        # cms_extension attribute has been added to all app configs
        # that define a cms extension class
        self.assertFalse(hasattr(non_cms_app, 'cms_extension'))
        self.assertTrue(hasattr(feature_app, 'cms_extension'))
        self.assertFalse(hasattr(config_app, 'cms_extension'))
        self.assertTrue(hasattr(feature_and_config_app, 'cms_extension'))

        # Code from the configure method did what we expected.
        # Relying on checking that the code in the app_with_cms_feature
        # test app ran. This is so as to avoid mocking and allow the
        # whole app registration code to run through.
        self.assertEqual(feature_app.cms_extension.num_configured_apps, 1)
        self.assertListEqual(
            feature_app.cms_extension.configured_apps,
            ['app_with_cms_config'])
