from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppExtension, CMSAppConfig
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.wizards.wizard_base import Wizard


class CMSCoreConfig(CMSAppConfig):
    cms_enabled = True
    cms_wizards = [cms_page_wizard, cms_subpage_wizard]


class CMSCoreExtensions(CMSAppExtension):

    def __init__(self):
        self.wizards = {}  # this is instead of wizard_pool._entries

    def configure_wizards(self, cms_config):
        if not hasattr(cms_config, 'cms_wizards'):
            # The cms_wizards settings is optional. If it's not here
            # just move on.
            return
        if type(cms_config.cms_wizards) != list:
            raise ImproperlyConfigured("cms_wizards must be a list")
        for wizard in cms_config.cms_wizards:
            if not isinstance(wizard, Wizard):
                raise ImproperlyConfigured(
                    "all wizards defined in cms_wizards must inherit "
                    "from cms.wizards.wizard_base.Wizard")
        for wizard in cms_config.cms_wizards:
            self.wizards[wizard.id] = wizard

    def configure_app(self, cms_config):
        self.configure_wizards(cms_config)
