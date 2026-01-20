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


class CMSAppConfigGetContractTestCase(CMSTestCase):
    """Tests for CMSAppConfig.get_contract() method."""

    def setUp(self):
        # Clear cache for get_cms_extension_apps
        app_registration.get_cms_extension_apps.cache_clear()

    def test_get_contract_returns_none_when_no_extensions_exist(self):
        """Test that get_contract returns None when no CMS extensions are registered."""
        from cms.app_base import CMSAppConfig

        result = CMSAppConfig.get_contract('non_existent_contract')
        self.assertIsNone(result)

    @override_settings(INSTALLED_APPS=[
        'cms.test_utils.project.app_with_cms_feature',
    ])
    def test_get_contract_returns_none_when_contract_not_found(self):
        """Test that get_contract returns None when contract name doesn't match any registered contract."""
        from cms.app_base import CMSAppConfig

        app_registration.autodiscover_cms_configs()

        result = CMSAppConfig.get_contract('non_existent_contract')
        self.assertIsNone(result)

    def test_get_contract_with_mocked_extension(self):
        """Test that get_contract correctly retrieves a contract from a mocked extension."""
        from cms.app_base import CMSAppConfig

        # Create a mock app with a contract
        mock_extension = Mock()
        contract_obj = Mock()
        contract_obj.some_method = Mock(return_value='contract_result')
        mock_extension.contract = ('test_contract', contract_obj)

        mock_app = Mock()
        mock_app.cms_extension = mock_extension

        # Patch get_cms_extension_apps to return our mock
        with patch.object(app_registration, 'get_cms_extension_apps', return_value=[mock_app]):
            result = CMSAppConfig.get_contract('test_contract')

            # Verify the contract was returned
            self.assertEqual(result, contract_obj)
            # Verify we can use the returned contract
            self.assertEqual(result.some_method(), 'contract_result')

    def test_get_contract_returns_none_when_extension_has_no_contract(self):
        """Test that get_contract returns None when extension doesn't define a contract attribute."""
        from cms.app_base import CMSAppConfig

        # Create a mock app without a contract attribute
        mock_extension = Mock(spec=[])  # No contract attribute
        mock_app = Mock()
        mock_app.cms_extension = mock_extension

        with patch.object(app_registration, 'get_cms_extension_apps', return_value=[mock_app]):
            result = CMSAppConfig.get_contract('test_contract')
            self.assertIsNone(result)

    def test_get_contract_stops_at_first_match(self):
        """Test that get_contract returns the first matching contract and stops searching."""
        from cms.app_base import CMSAppConfig

        # Create two mock apps with contracts
        contract_obj1 = Mock()
        mock_extension1 = Mock()
        mock_extension1.contract = ('matching_contract', contract_obj1)
        mock_app1 = Mock()
        mock_app1.cms_extension = mock_extension1

        contract_obj2 = Mock()
        mock_extension2 = Mock()
        mock_extension2.contract = ('matching_contract', contract_obj2)
        mock_app2 = Mock()
        mock_app2.cms_extension = mock_extension2

        with patch.object(app_registration, 'get_cms_extension_apps',
                         return_value=[mock_app1, mock_app2]):
            result = CMSAppConfig.get_contract('matching_contract')

            # Should return the first contract, not the second
            self.assertEqual(result, contract_obj1)
            self.assertNotEqual(result, contract_obj2)


class ConfigureCmsAppsTestCase(CMSTestCase):
    """Tests for configure_cms_apps() function."""

    def setUp(self):
        # Clear cache for get_cms_config_apps
        app_registration.get_cms_config_apps.cache_clear()

    def test_configure_cms_apps_uses_contract_name_as_enabled_property(self):
        """Test that configure_cms_apps respects the contract name when determining enabled property."""
        # Create mock extension with a custom contract name
        mock_extension = Mock()
        contract_obj = Mock()
        mock_extension.contract = ('versioning', contract_obj)
        mock_extension.configure_app = Mock()

        mock_feature_app = Mock()
        mock_feature_app.cms_extension = mock_extension
        mock_feature_app.label = 'my_feature'

        # Create mock config app with versioning_enabled = True
        mock_cms_config = Mock()
        mock_cms_config.versioning_enabled = True
        mock_config_app = Mock()
        mock_config_app.cms_config = mock_cms_config

        with patch.object(app_registration, 'get_cms_config_apps',
                         return_value=[mock_config_app]):
            app_registration.configure_cms_apps([mock_feature_app])

            # configure_app should be called because versioning_enabled = True
            mock_extension.configure_app.assert_called_once_with(mock_cms_config)

    def test_configure_cms_apps_uses_app_label_when_no_contract(self):
        """Test that configure_cms_apps uses app label as contract name when no contract is defined."""
        # Create mock extension without a contract attribute
        mock_extension = Mock(spec=['configure_app'])
        mock_extension.configure_app = Mock()

        mock_feature_app = Mock()
        mock_feature_app.cms_extension = mock_extension
        mock_feature_app.label = 'my_feature'

        # Create mock config app with my_feature_enabled = True
        mock_cms_config = Mock()
        mock_cms_config.my_feature_enabled = True
        mock_config_app = Mock()
        mock_config_app.cms_config = mock_cms_config

        with patch.object(app_registration, 'get_cms_config_apps',
                         return_value=[mock_config_app]):
            app_registration.configure_cms_apps([mock_feature_app])

            # configure_app should be called because my_feature_enabled = True
            mock_extension.configure_app.assert_called_once_with(mock_cms_config)

    def test_configure_cms_apps_skips_disabled_apps(self):
        """Test that configure_cms_apps doesn't configure apps where enabled property is False."""
        # Create mock extension with custom contract name
        mock_extension = Mock()
        mock_extension.contract = ('versioning', Mock())
        mock_extension.configure_app = Mock()

        mock_feature_app = Mock()
        mock_feature_app.cms_extension = mock_extension

        # Create mock config app with versioning_enabled = False
        mock_cms_config = Mock()
        mock_cms_config.versioning_enabled = False
        mock_config_app = Mock()
        mock_config_app.cms_config = mock_cms_config

        with patch.object(app_registration, 'get_cms_config_apps',
                         return_value=[mock_config_app]):
            app_registration.configure_cms_apps([mock_feature_app])

            # configure_app should NOT be called because versioning_enabled = False
            mock_extension.configure_app.assert_not_called()

    def test_configure_cms_apps_raises_error_on_invalid_contract(self):
        """Test that configure_cms_apps raises ImproperlyConfigured for invalid contract format."""
        # Create mock extension with invalid contract (not a tuple)
        mock_extension = Mock()
        mock_extension.contract = 'invalid_contract'

        mock_feature_app = Mock()
        mock_feature_app.cms_extension = mock_extension

        with self.assertRaises(ImproperlyConfigured) as context:
            app_registration.configure_cms_apps([mock_feature_app])

        self.assertIn('2-tuple', str(context.exception))

    def test_configure_cms_apps_with_multiple_configs(self):
        """Test that configure_cms_apps configures multiple apps with matching enabled property."""
        # Create mock extension with contract name
        mock_extension = Mock()
        mock_extension.contract = ('versioning', Mock())
        mock_extension.configure_app = Mock()

        mock_feature_app = Mock()
        mock_feature_app.cms_extension = mock_extension

        # Create two mock config apps, both with versioning_enabled = True
        mock_cms_config1 = Mock()
        mock_cms_config1.versioning_enabled = True
        mock_config_app1 = Mock()
        mock_config_app1.cms_config = mock_cms_config1

        mock_cms_config2 = Mock()
        mock_cms_config2.versioning_enabled = True
        mock_config_app2 = Mock()
        mock_config_app2.cms_config = mock_cms_config2

        with patch.object(app_registration, 'get_cms_config_apps',
                         return_value=[mock_config_app1, mock_config_app2]):
            app_registration.configure_cms_apps([mock_feature_app])

            # configure_app should be called twice
            self.assertEqual(mock_extension.configure_app.call_count, 2)
            calls = [call[0][0] for call in mock_extension.configure_app.call_args_list]
            self.assertIn(mock_cms_config1, calls)
            self.assertIn(mock_cms_config2, calls)
