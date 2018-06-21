import inspect
from importlib import import_module

from django.apps import apps
from django.utils.module_loading import module_has_submodule
from django.core.exceptions import ImproperlyConfigured


CMS_CONFIG_NAME = 'cms_apps'


def autodiscover_cms_configs():
    """
    Find and import all cms_apps.py files. Add a cms_app attribute
    to django's app config with an instance of the cms config.
    """
    for app_config in apps.get_app_configs():
        try:
            cms_module = import_module(
                '%s.%s' % (app_config.name, CMS_CONFIG_NAME))
        except:
            # If something in cms_apps.py raises an exception let that
            # exception bubble up. Only catch the exception if
            # cms_apps.py doesn't exist
            if module_has_submodule(app_config.module, CMS_CONFIG_NAME):
                raise
        else:
            cms_app_classes = []
            # Find all classes that inherit from CMSAppConfig
            for name, obj in inspect.getmembers(cms_module):
                is_cms_app_config = (
                    inspect.isclass(obj) and
                    issubclass(obj, CMSAppConfig) and
                    # Ignore the import of CMSAppConfig itself
                    obj != CMSAppConfig
                )
                if is_cms_app_config:
                    cms_app_classes.append(obj)

            if len(cms_app_classes) == 1:
                # We are adding this attribute here rather than in
                # django's app config definition because there are
                # all kinds of limitations as to what can be imported
                # in django's apps.py and this could cause issues
                app_config.cms_app = cms_app_classes[0]()
            #~ else:
                #~ raise ImproperlyConfigured(
                    #~ "cms_apps.py files must define exactly one "
                    #~ "class which inherits from CMSAppConfig")


def get_cms_apps_with_features():
    """
    Returns app configs of apps with cms features
    """
    apps_with_features = []

    for app_config in apps.get_app_configs():
        # The cms_app attr is added by the autodiscover_cms_configs
        # function if a cms_apps.py file with a suitable class is found.
        is_cms_app = hasattr(app_config, 'cms_app')
        if is_cms_app:
            # The configure_app method is only present on the cms
            # app class if the app provides a cms feature. For classes
            # that only have config this method will not be present.
            has_cms_extension = hasattr(
                app_config.cms_app, 'configure_app')
        else:
            has_cms_extension = False
        if is_cms_app and has_cms_extension:
            apps_with_features.append(app_config)

    return apps_with_features


def configure_cms_apps(apps_with_features):
    """
    Check installed apps for apps that are configured to use cms addons
    and run code to register them with their config
    """
    for app_with_feature in apps_with_features:
        enabled_property = "{app_label}_enabled".format(
            app_label=app_with_feature.label)
        configure_app = app_with_feature.cms_app.configure_app

        for app_config in apps.get_app_configs():
            if not hasattr(app_config, 'cms_app'):
                # Not a cms app, so ignore
                continue
            if getattr(app_config.cms_app, enabled_property, False):
                # Feature enabled for this app so configure
                configure_app(app_config)


class CMSAppConfig():
    pass
