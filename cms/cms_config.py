from logging import getLogger
from collections import Iterable

from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppExtension, CMSAppConfig
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.wizards.wizard_base import Wizard


logger = getLogger(__name__)


class CMSCoreConfig(CMSAppConfig):
    cms_enabled = True
    cms_wizards = [cms_page_wizard, cms_subpage_wizard]


class CMSCoreExtensions(CMSAppExtension):

    def __init__(self):
        self.wizards = {}

    def configure_wizards(self, cms_config):
        """
        Adds all registered wizards from apps that define them to the
        wizards dictionary on this class
        """
        if not isinstance(cms_config.cms_wizards, Iterable):
            raise ImproperlyConfigured("cms_wizards must be iterable")
        for wizard in cms_config.cms_wizards:
            if not isinstance(wizard, Wizard):
                raise ImproperlyConfigured(
                    "All wizards defined in cms_wizards must inherit "
                    "from cms.wizards.wizard_base.Wizard"
                )
            elif wizard.id in self.wizards:
                msg = "Wizard for model {} has already been registered".format(
                    wizard.get_model()
                )
                logger.warning(msg)
            else:
                self.wizards[wizard.id] = wizard

    def configure_app(self, cms_config):
        # The cms_wizards settings is optional. If it's not here
        # just move on.
        if hasattr(cms_config, 'cms_wizards'):
            self.configure_wizards(cms_config)
