import inspect
from importlib import import_module

from django.apps import apps
from django.utils.module_loading import module_has_submodule


CMS_CONFIG_NAME = 'cms_apps'


def autodiscover_cms_files():
    """
    Find and import all cms_apps.py modules. Add a cms_app attribute
    to django's app config.
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
            for name, obj in inspect.getmembers(cms_module):
                if inspect.isclass(obj) and CMSAppConfig in obj.__mro__:
                    # We are adding this attribute here rather than in
                    # django's app config definition because there are
                    # all kinds of limitations as to what can be
                    # imported in django's apps.py and this could cause
                    # issues
                    app_config.cms_app = obj()


class CMSAppConfig():
    pass
