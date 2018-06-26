# -*- coding: utf-8 -*-
import inspect
from importlib import import_module

from django.apps import apps
from django.utils.lru_cache import lru_cache
from django.utils.module_loading import module_has_submodule
from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.constants import CMS_CONFIG_NAME


def _find_subclasses(module, klass):
    """
    Helper function.

    Returns a list of classes in module which inherit from klass.
    """
    classes = []
    # Find all classes that inherit from klass
    for name, obj in inspect.getmembers(module):
        is_subclass = (
            inspect.isclass(obj) and
            issubclass(obj, klass) and
            # Ignore the import of klass itself
            obj != klass
        )
        if is_subclass:
            classes.append(obj)
    return classes


def _find_config(cms_module):
    """
    Helper function.

    Returns the class inheriting from CMSAppConfig in the given module.
    If no such class exists in the module, returns None.
    If multiple classes inherit from CMSAppConfig, raises
    ImproperlyConfigured exception.
    """
    cms_config_classes = _find_subclasses(cms_module, CMSAppConfig)
    if len(cms_config_classes) == 1:
        return cms_config_classes[0]
    elif len(cms_config_classes) > 1:
        raise ImproperlyConfigured(
            "cms_config.py files can't define more than one "
            "class which inherits from CMSAppConfig")


def _find_extension(cms_module):
    """
    Helper function.

    Returns the class inheriting from CMSAppExtension in the given module.
    If no such class exists in the module, returns None.
    If multiple classes inherit from CMSAppExtension, raises
    ImproperlyConfigured exception.
    """
    cms_extension_classes = _find_subclasses(cms_module, CMSAppExtension)
    if len(cms_extension_classes) == 1:
        return cms_extension_classes[0]
    elif len(cms_extension_classes) > 1:
        raise ImproperlyConfigured(
            "cms_config.py files can't define more than one "
            "class which inherits from CMSAppExtension")


def autodiscover_cms_configs():
    """
    Find and import all cms_config.py files. Add a cms_app attribute
    to django's app config with an instance of the cms config.
    """
    for app_config in apps.get_app_configs():
        try:
            cms_module = import_module(
                '%s.%s' % (app_config.name, CMS_CONFIG_NAME))
        except:
            # If something in cms_config.py raises an exception let that
            # exception bubble up. Only catch the exception if
            # cms_config.py doesn't exist
            if module_has_submodule(app_config.module, CMS_CONFIG_NAME):
                raise
        else:
            config = _find_config(cms_module)
            extension = _find_extension(cms_module)
            # We are adding these attributes here rather than in
            # django's app config definition because there are
            # all kinds of limitations as to what can be imported
            # in django's apps.py and leaving it to devs to define this
            # there could cause issues
            if config:
                app_config.cms_config = config(app_config)
            if extension:
                app_config.cms_extension = extension()
            if not config and not extension:
                raise ImproperlyConfigured(
                    "cms_config.py files must define at least one "
                    "class which inherits from CMSAppConfig or "
                    "CMSAppExtension")


@lru_cache(maxsize=None)
def get_cms_extension_apps():
    """
    Returns django app configs of apps with a cms extension
    """
    # NOTE: The cms_extension attr is added by the autodiscover_cms_configs
    # function if a cms_config.py file with a suitable class is found.
    cms_apps = [app_config for app_config in apps.get_app_configs()
                if hasattr(app_config, 'cms_extension')]
    return cms_apps


@lru_cache(maxsize=None)
def get_cms_config_apps():
    """
    Returns django app configs of apps with a cms config
    """
    # NOTE: The cms_config attr is added by the autodiscover_cms_configs
    # function if a cms_config.py file with a suitable class is found.
    cms_apps = [app_config for app_config in apps.get_app_configs()
                if hasattr(app_config, 'cms_config')]
    return cms_apps


def configure_cms_apps(apps_with_features):
    """
    Check installed apps for apps that are configured to use cms addons
    and run code to register them with their config
    """
    for app_with_feature in apps_with_features:
        enabled_property = "{}_enabled".format(app_with_feature.label)
        configure_app = app_with_feature.cms_extension.configure_app

        for app_config in get_cms_config_apps():
            if getattr(app_config.cms_config, enabled_property, False):
                # Feature enabled for this app so configure
                configure_app(app_config.cms_config)
