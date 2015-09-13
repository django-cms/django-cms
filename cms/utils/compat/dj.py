from django.conf import settings

__all__ = ['is_installed', 'installed_apps', 'get_apps', 'get_app_paths']

# import these directly from Django!
from django.utils.encoding import (  # nopyflakes
    force_text as force_unicode, python_2_unicode_compatible,
)

try:  # pragma: no cover
    from django.apps import apps

    def is_installed(app_name):
        return apps.is_installed(app_name)

    def installed_apps():
        return [app.name for app in apps.get_app_configs()]

    def get_app_paths():
        return [app.path for app in apps.get_app_configs()]

    def get_apps():
        return [app.models_module for app in apps.get_app_configs()]

except ImportError:  # Django 1.6

    def is_installed(app_name):
        return app_name in settings.INSTALLED_APPS

    def installed_apps():
        return settings.INSTALLED_APPS

    from django.db.models.loading import get_app_paths, get_apps

try:
    from django.utils.translation import LANGUAGE_SESSION_KEY
except ImportError:
    LANGUAGE_SESSION_KEY = 'django_language'
