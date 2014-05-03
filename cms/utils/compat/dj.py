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
    from django.conf import settings

    def is_installed(app_name):
        return app_name in settings.INSTALLED_APPS

    def installed_apps():
        return settings.INSTALLED_APPS