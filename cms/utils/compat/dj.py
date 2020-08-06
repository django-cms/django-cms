import six

from functools import WRAPPER_ASSIGNMENTS

from django.apps import apps
from django.conf import settings


__all__ = ['is_installed', 'installed_apps', 'get_apps', 'get_app_paths']

def is_installed(app_name):
    return apps.is_installed(app_name)

def installed_apps():
    return [app.name for app in apps.get_app_configs()]

def available_attrs(fn):
    return WRAPPER_ASSIGNMENTS
