from django.apps import apps

__all__ = ['is_installed', 'installed_apps', 'get_apps', 'get_app_paths']

# import these directly from Django!
from django.utils.encoding import (  # nopyflakes
    force_text as force_unicode, python_2_unicode_compatible,
)

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    class MiddlewareMixin(object): pass


# TODO: move these helpers out of compat?
def is_installed(app_name):
    return apps.is_installed(app_name)

def installed_apps():
    return [app.name for app in apps.get_app_configs()]

def get_app_paths():
    return [app.path for app in apps.get_app_configs()]

def get_apps():
    return [app.models_module for app in apps.get_app_configs()]
