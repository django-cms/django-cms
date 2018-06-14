from importlib import import_module

from django.apps import apps
from django.utils.module_loading import module_has_submodule


CMS_CONFIG_NAME = 'cms_apps'


def autodiscover_cms_files():
    """Find and import all cms_apps.py modules"""
    for app_config in apps.get_app_configs():
        try:
            import_module('%s.%s' % (app_config.name, CMS_CONFIG_NAME))
        except Exception:
            if module_has_submodule(app_config.module, CMS_CONFIG_NAME):
                raise


class CMSAppConfig():
    # Temporary stub
    pass


class CMSAppExtension():
    # Temporary stub
    pass
