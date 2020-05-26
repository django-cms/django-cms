import six

from functools import WRAPPER_ASSIGNMENTS

from django.apps import apps
from django.conf import settings


__all__ = ['is_installed', 'installed_apps', 'get_apps', 'get_app_paths']

# import these directly from Django!
from django.utils.encoding import (  # nopyflakes
    force_text as force_unicode,
)

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    class MiddlewareMixin(object): pass

try:
    from django.urls import URLResolver  # nopyflakes
    from django.urls.resolvers import RegexPattern, URLPattern  # nopyflakes
except ImportError:
    # django 1.11 support
    from django.core.urlresolvers import RegexURLResolver as URLResolver, RegexURLPattern as URLPattern  # nopyflakes
    class RegexPattern: pass

try:
    from django.urls import LocalePrefixPattern  # nopyflakes
except ImportError:
    # Only for django 1.11
    from django.core.urlresolvers import LocaleRegexURLResolver as LocalePrefixPattern  # nopyflakes


# TODO: move these helpers out of compat?
def is_installed(app_name):
    return apps.is_installed(app_name)

def installed_apps():
    return [app.name for app in apps.get_app_configs()]

def get_app_paths():
    return [app.path for app in apps.get_app_configs()]

def get_apps():
    return [app.models_module for app in apps.get_app_configs()]

def available_attrs(fn):
    if six.PY3:
        return WRAPPER_ASSIGNMENTS
    else:
        return tuple(a for a in WRAPPER_ASSIGNMENTS if hasattr(fn, a))

def get_middleware():
    return settings.MIDDLEWARE
