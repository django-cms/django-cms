import django
from django.conf import settings

__all__ = ['User', 'get_user_model', 'user_model_label', 'user_related_name',
           'user_related_query_name',
           'python_2_unicode_compatible', 'get_app_paths',
           'is_installed', 'installed_apps'
           ]


try:
    from django.utils.encoding import force_unicode
    def python_2_unicode_compatible(klass):
        """
        A decorator that defines __unicode__ and __str__ methods under Python 2.
        Under Python 3 it does nothing.

        To support Python 2 and 3 with a single code base, define a __str__ method
        returning text and apply this decorator to the class.
        """
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda self: self.__unicode__().encode('utf-8')
        return klass
except ImportError:
    force_unicode = lambda s: str(s)
    from django.utils.encoding import python_2_unicode_compatible  # nopyflakes

try:
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

try:
    from django.apps import apps

    def is_installed(app_name):
        return apps.is_installed(app_name)

    def installed_apps():
        return [app.name for app in apps.get_app_configs()]

except ImportError:

    def is_installed(app_name):
        return app_name in settings.INSTALLED_APPS

    def installed_apps():
        return settings.INSTALLED_APPS


# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import User as OriginalUser
    is_user_swapped = bool(OriginalUser._meta.swapped)
else:
    from django.contrib.auth.models import User
    User.USERNAME_FIELD = 'username'
    get_user_model = lambda: User
    is_user_swapped = False

user_model_label = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# With a custom user model named "EmailUser", Django 1.5 creates
# Group.emailuser_set but Django 1.6 creates Group.user_set.
# See https://code.djangoproject.com/ticket/20244
if (1, 5) <= django.VERSION < (1, 6):
    user_related_query_name = user_model_label.split('.')[1].lower()
    user_related_name = user_related_query_name + '_set'
else:
    user_related_query_name = "user"
    user_related_name = "user_set"