from collections.abc import Iterable
from functools import cached_property
from logging import getLogger

from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.models import PageContent
from cms.page_rendering import render_pagecontent
from cms.wizards.wizard_base import Wizard

logger = getLogger(__name__)


class CMSCoreConfig(CMSAppConfig):
    cms_enabled = True
    cms_wizards = [cms_page_wizard, cms_subpage_wizard]
    cms_toolbar_enabled_models = [(PageContent, render_pagecontent, "page")]


class CMSCoreExtensions(CMSAppExtension):
    def __init__(self):
        self.lazy_wizards = []
        self.toolbar_enabled_models = {}
        self.model_groupers = {}
        self.toolbar_mixins = []

    def configure_wizards(self, cms_config):
        """
        Adds all registered wizards from apps that define them to the
        wizards dictionary on this class
        """
        if not isinstance(cms_config.cms_wizards, Iterable):
            raise ImproperlyConfigured("cms_wizards must be iterable")

        self.lazy_wizards.append(cms_config.cms_wizards)

    @cached_property
    def wizards(self) -> dict[str, Wizard]:
        """
        Returns a dictionary of wizard instances keyed by their unique IDs.
        Iterates over all iterables in `self.lazy_wizards`, filters out objects that are instances
        of the `Wizard` class, and constructs a dictionary where each key is the wizard's `id`
        and the value is the corresponding `Wizard` instance.
        Returns:
            dict: A dictionary mapping wizard IDs to `Wizard` instances.
        """

        wizards = {}
        for iterable in self.lazy_wizards:
            new_wizards = {wizard.id: wizard for wizard in iterable}
            if wizard := next((wizard for wizard in new_wizards.values() if not isinstance(wizard, Wizard)), None):
                # If any wizard in the iterable is not an instance of Wizard, raise an exception
                raise ImproperlyConfigured(
                    f"cms_wizards must be iterable of Wizard instances, got {type(wizard)}"
                )
            wizards |= new_wizards
        return wizards

    def configure_toolbar_enabled_models(self, cms_config):
        if not isinstance(cms_config.cms_toolbar_enabled_models, Iterable):
            raise ImproperlyConfigured("cms_toolbar_enabled_models must be iterable")
        for model, render_func, *grouper in cms_config.cms_toolbar_enabled_models:
            if model in self.toolbar_enabled_models:
                logger.warning(
                    f"Model {model} already registered for frontend rendering",
                )
            else:
                self.toolbar_enabled_models[model] = render_func
                if grouper:
                    self.model_groupers[model] = grouper[0]

    def configure_toolbar_mixin(self, cms_config):
        if not issubclass(cms_config.cms_toolbar_mixin, object):
            raise ImproperlyConfigured("cms_toolbar_mixin must be class")
        self.toolbar_mixins.append(cms_config.cms_toolbar_mixin)

    def configure_app(self, cms_config):
        # The cms_wizards settings is optional. If it's not here
        # just move on.
        if hasattr(cms_config, 'cms_wizards'):
            self.configure_wizards(cms_config)
        if hasattr(cms_config, 'cms_toolbar_enabled_models'):
            self.configure_toolbar_enabled_models(cms_config)
        if hasattr(cms_config, 'cms_toolbar_mixin'):
            self.configure_toolbar_mixin(cms_config)
