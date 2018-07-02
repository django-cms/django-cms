from mock import Mock

from django.apps import apps

from cms.cms_config import CMSCoreExtensions
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.test_utils.project.sampleapp.cms_wizards import sample_wizard
from cms.test_utils.testcases import CMSTestCase
from cms.utils.setup import setup_cms_apps


class ConfigureWizardsUnitTestCase(CMSTestCase):

    def test_adds_wizards_to_dict(self):
        extensions = CMSCoreExtensions()
        wizard1 = Mock(id=111)
        wizard2 = Mock(id=222)
        cms_config = Mock(
            cms_enabled=True, cms_wizards=[wizard1, wizard2])

        extensions.configure_wizards(cms_config)

        self.assertDictEqual(
            extensions.wizards, {111: wizard1, 222: wizard2})

    def test_doesnt_raise_exception_when_wizards_dict_undefined(self):
        extensions = CMSCoreExtensions()
        cms_config = Mock(cms_enabled=True, spec=[])

        try:
            extensions.configure_wizards(cms_config)
        except AttributeError:
            self.fail("Raises exception when cms_wizards undefined")


class ConfigureWizardsIntegrationTestCase(CMSTestCase):

    def test_adds_all_wizards_to_dict(self):
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
