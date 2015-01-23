from django.conf import settings

__all__ = [
    'user_model_label', 'get_app_paths', 'is_installed', 'installed_apps',
]

# import these directly from Django!
from django.utils.encoding import (  # nopyflakes
    force_text as force_unicode, python_2_unicode_compatible,
)


try:  # pragma: no cover
    from django.db.models.loading import get_app_paths
except ImportError:
    from django.db.models.loading import get_apps
    try:
        from django.utils._os import upath
    except ImportError:
        upath = lambda path: path

    def get_app_paths():
        """
        Returns a list of paths to all installed apps.

        Useful for discovering files at conventional locations inside apps
        (static files, templates, etc.)
        """
        app_paths = []
        for app in get_apps():
            if hasattr(app, '__path__'):        # models/__init__.py package
                app_paths.extend([upath(path) for path in app.__path__])
            else:                               # models.py module
                app_paths.append(upath(app.__file__))
        return app_paths

try:  # pragma: no cover
    from django.apps import apps

    def is_installed(app_name):
        return apps.is_installed(app_name)

    def installed_apps():
        return [app.name for app in apps.get_app_configs()]

except ImportError:  # Django 1.6

    def is_installed(app_name):
        return app_name in settings.INSTALLED_APPS

    def installed_apps():
        return settings.INSTALLED_APPS


from django.contrib.auth.models import User as OriginalUser
is_user_swapped = bool(OriginalUser._meta.swapped)
user_model_label = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
