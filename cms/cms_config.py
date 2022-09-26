from logging import getLogger
from collections.abc import Iterable

from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppExtension, CMSAppConfig
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.models import PageContent
from cms.page_rendering import render_pagecontent
from cms.wizards.wizard_base import Wizard


logger = getLogger(__name__)


class CMSCoreConfig(CMSAppConfig):
    cms_enabled = True
    cms_wizards = [cms_page_wizard, cms_subpage_wizard]
    cms_toolbar_enabled_models = [(PageContent, render_pagecontent)]


class CMSCoreExtensions(CMSAppExtension):

    def __init__(self):
        self.wizards = {}
        self.toolbar_enabled_models = {}

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

    def configure_toolbar_enabled_models(self, cms_config):
        if not isinstance(cms_config.cms_toolbar_enabled_models, Iterable):
            raise ImproperlyConfigured("cms_toolbar_enabled_models must be iterable")
        for model, render_func in cms_config.cms_toolbar_enabled_models:
            if model in self.toolbar_enabled_models:
                logger.warning(
                    "Model {} already registered for frontend rendering".format(model),
                )
            else:
                self.toolbar_enabled_models[model] = render_func

    def configure_app(self, cms_config):
        # The cms_wizards settings is optional. If it's not here
        # just move on.
        if hasattr(cms_config, 'cms_wizards'):
            self.configure_wizards(cms_config)
        if hasattr(cms_config, 'cms_toolbar_enabled_models'):
            self.configure_toolbar_enabled_models(cms_config)
