from unittest.mock import Mock, patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from cms.app_registration import get_cms_config_apps, get_cms_extension_apps
from cms.cms_config import CMSCoreExtensions
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.test_utils.project.sampleapp.cms_wizards import sample_wizard
from cms.test_utils.testcases import CMSTestCase
from cms.utils.setup import setup_cms_apps
from cms.wizards.wizard_base import Wizard


class ConfigureWizardsUnitTestCase(CMSTestCase):

    def test_adds_wizards_to_dict(self):
        """
        If the wizard setting is correctly defined, add the wizards to the
        dictionary of wizards
        """
        extensions = CMSCoreExtensions()
        wizard1 = Mock(id=111, spec=Wizard)
        wizard2 = Mock(id=222, spec=Wizard)
        cms_config = Mock(
            cms_enabled=True, cms_wizards=[wizard1, wizard2])
        extensions.configure_wizards(cms_config)
        self.assertDictEqual(
            extensions.wizards, {111: wizard1, 222: wizard2})

    def test_doesnt_raise_exception_when_wizards_dict_undefined(self):
        """
        If the wizard setting is not present in the config, simply
        ignore this. The wizard setting is optional.
        """
        extensions = CMSCoreExtensions()
        cms_config = Mock(cms_enabled=True, spec=[])
        try:
            extensions.configure_app(cms_config)
        except AttributeError:
            self.fail("Raises exception when cms_wizards undefined")

    def test_raises_exception_if_doesnt_inherit_from_wizard_class(self):
        """
        If one or more of the wizards defined in the wizard setting
        do not inherit from the Wizard class, raise an exception
        """
        extensions = CMSCoreExtensions()
        wizard = Mock(id=3, spec=object)
        cms_config = Mock(
            cms_enabled=True, cms_wizards=[wizard])
        extensions.configure_wizards(cms_config)
        with self.assertRaises(ImproperlyConfigured):
            extensions.wizards


    def test_raises_exception_if_not_iterable(self):
        """
        If the wizard setting isn't iterable, raise an exception.
        """
        extensions = CMSCoreExtensions()
        wizard = Mock(id=6, spec=Wizard)
        cms_config = Mock(
            cms_enabled=True, cms_wizards=wizard)
        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_wizards(cms_config)


class ConfigureWizardsIntegrationTestCase(CMSTestCase):

    def setUp(self):
        # The results of get_cms_extension_apps and get_cms_config_apps
        # are cached. Clear this cache because installed apps change
        # between tests and therefore unlike in a live environment,
        # results of this function can change between tests
        get_cms_extension_apps.cache_clear()
        get_cms_config_apps.cache_clear()

    def test_adds_all_wizards_to_dict(self):
        """
        Check that all wizards are picked up from both cms.cms_config
        and sampleapp.cms_config
        """
        setup_cms_apps()
        app = apps.get_app_config('cms')
        # cms core defines wizards in its config, as does sampleapp
        # all of these wizards should have been picked up and added
        expected_wizards = {
            cms_page_wizard.id: cms_page_wizard,
            cms_subpage_wizard.id: cms_subpage_wizard,
            sample_wizard.id: sample_wizard,
        }
        self.assertDictEqual(app.cms_extension.wizards, expected_wizards)
