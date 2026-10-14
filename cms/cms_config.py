from collections.abc import Iterable, Mapping
from functools import cached_property
from logging import getLogger

from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard
from cms.core import (
    queries as core_queries,  # noqa: F401  -- registers the placeholder and plugin lookups
    services as plugin_services,  # noqa: F401  -- declares the plugin operations
)
from cms.extensions import services as extension_services  # noqa: F401  -- declares the extension operations
from cms.models import PageContent
from cms.operations import Operation, Query, register_operation, register_query
from cms.pages import (
    checks as page_checks,  # noqa: F401  -- registers the page operation checks
    editing,  # noqa: F401  -- registers the page editing hooks
    queries as page_queries,  # noqa: F401  -- registers the page content lookup
    services as page_services,  # noqa: F401  -- declares the page operations
)
from cms.pages.rendering import render_pagecontent
from cms.permissions import (
    checks as permission_checks,  # noqa: F401  -- registers the grant checks
    services as permission_services,  # noqa: F401  -- declares the grant operations
)
from cms.shared.checks import VALIDATION, register_check
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

    def configure_checks(self, cms_config):
        """Registers the operation checks of an app, see :mod:`cms.shared.checks`.

        ``cms_checks`` maps an operation name to ``(name, check)``,
        ``(name, check, requires)`` or ``(name, check, requires, kind)`` tuples.
        ``kind`` is ``"permission"``, ``"policy"`` or ``"validation"`` (the default).
        """
        if not isinstance(cms_config.cms_checks, Mapping):
            raise ImproperlyConfigured("cms_checks must be a mapping of operation names to checks")
        for operation, checks in cms_config.cms_checks.items():
            for name, check, *options in checks:
                if not callable(check):
                    raise ImproperlyConfigured(f"Check {name!r} for {operation!r} is not callable")
                requires = options[0] if options else ()
                kind = options[1] if len(options) > 1 else VALIDATION
                try:
                    register_check(operation, name, check, requires=requires, kind=kind)
                except ValueError as error:
                    raise ImproperlyConfigured(str(error)) from error

    def configure_operations(self, cms_config):
        """Declares the operations of an app, see :mod:`cms.operations`.

        ``cms_operations`` is a list of :class:`~cms.operations.Operation`.
        """
        if not isinstance(cms_config.cms_operations, Iterable):
            raise ImproperlyConfigured("cms_operations must be a list of Operation declarations")
        for declaration in cms_config.cms_operations:
            if not isinstance(declaration, Operation):
                raise ImproperlyConfigured(f"{declaration!r} in cms_operations is not an Operation")
            try:
                register_operation(declaration)
            except ValueError as error:
                raise ImproperlyConfigured(str(error)) from error

    def configure_editability_checks(self, cms_config):
        """Registers an app's editability checks, see :func:`cms.core.checks.register_editability_check`.

        ``cms_editability_checks`` is a list of ``(name, check)`` tuples.
        """
        from cms.core.checks import register_editability_check

        for name, check in cms_config.cms_editability_checks:
            if not callable(check):
                raise ImproperlyConfigured(f"Editability check {name!r} is not callable")
            register_editability_check(name, check)

    def configure_queries(self, cms_config):
        """Declares the reads of an app, see :mod:`cms.operations`.

        ``cms_queries`` is a list of :class:`~cms.operations.Query`.
        """
        if not isinstance(cms_config.cms_queries, Iterable):
            raise ImproperlyConfigured("cms_queries must be a list of Query declarations")
        for declaration in cms_config.cms_queries:
            if not isinstance(declaration, Query):
                raise ImproperlyConfigured(f"{declaration!r} in cms_queries is not a Query")
            try:
                register_query(declaration)
            except ValueError as error:
                raise ImproperlyConfigured(str(error)) from error

    def configure_app(self, cms_config):
        # The cms_wizards settings is optional. If it's not here
        # just move on.
        if hasattr(cms_config, 'cms_wizards'):
            self.configure_wizards(cms_config)
        if hasattr(cms_config, 'cms_toolbar_enabled_models'):
            self.configure_toolbar_enabled_models(cms_config)
        if hasattr(cms_config, 'cms_toolbar_mixin'):
            self.configure_toolbar_mixin(cms_config)
        if hasattr(cms_config, 'cms_operations'):
            self.configure_operations(cms_config)
        if hasattr(cms_config, 'cms_queries'):
            self.configure_queries(cms_config)
        if hasattr(cms_config, 'cms_checks'):
            self.configure_checks(cms_config)
        if hasattr(cms_config, 'cms_editability_checks'):
            self.configure_editability_checks(cms_config)
