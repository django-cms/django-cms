# -*- coding: utf-8 -*-
import inspect
from functools import lru_cache
from importlib import import_module

from django.apps import apps
from django.utils.module_loading import module_has_submodule
from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppConfig, CMSAppExtension


CMS_CONFIG_NAME = 'cms_config'


def _find_config(cms_module):
    cms_config_classes = []
    # Find all classes that inherit from CMSAppConfig
    for name, obj in inspect.getmembers(cms_module):
        is_cms_config = (
            inspect.isclass(obj) and
            issubclass(obj, CMSAppConfig) and
            # Ignore the import of CMSAppConfig itself
            obj != CMSAppConfig
        )
        if is_cms_config:
            cms_config_classes.append(obj)

    if len(cms_config_classes) == 1:
        return cms_config_classes[0]


def _find_extension(cms_module):
    cms_extension_classes = []
    # Find all classes that inherit from CMSAppExtension
    for name, obj in inspect.getmembers(cms_module):
        is_cms_extension = (
            inspect.isclass(obj) and
            issubclass(obj, CMSAppExtension) and
            # Ignore the import of CMSAppExtension itself
            obj != CMSAppExtension
        )
        if is_cms_extension:
            cms_extension_classes.append(obj)

    if len(cms_extension_classes) == 1:
        return cms_extension_classes[0]


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
                app_config.cms_config = config()
            if extension:
                app_config.cms_extension = extension()
            # TODO: What if has both but one doubled up
            if not config and not extension:
                raise ImproperlyConfigured(
                    "cms_config.py files must define one "
                    "class which inherits from CMSAppConfig and/or"
                    "one class which inherits from CMSAppExtension")


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


def configure_cms_apps(apps_with_features):
    """
    Check installed apps for apps that are configured to use cms addons
    and run code to register them with their config
    """
    for app_with_feature in apps_with_features:
        enabled_property = "{}_enabled".format(app_with_feature.label)
        configure_app = app_with_feature.cms_extension.configure_app

        for app_config in apps.get_app_configs():
            if not hasattr(app_config, 'cms_config'):
                # Not a cms app with a config, so ignore
                continue
            if getattr(app_config.cms_config, enabled_property, False):
                # Feature enabled for this app so configure
                configure_app(app_config)
