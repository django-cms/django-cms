# -*- coding: utf-8 -*-
"""
This is revision from 3058ab9d9d4875589638cc45e84b59e7e1d7c9c3 of
https://github.com/ojii/django-load.

ANY changes to this file, be it upstream fixes or changes for the cms *must* be
documented clearly within this file with comments.

For documentation on how to use the functions described in this file, please
refer to https://django-load.readthedocs.io/en/latest/index.html.
"""
import imp
import traceback # changed
from importlib import import_module

from django.utils.six.moves import filter, map

from .compat.dj import installed_apps


def get_module(app, modname, verbose, failfast):
    """
    Internal function to load a module from a single app.
    """
    module_name = '%s.%s' % (app, modname)
    # the module *should* exist - raise an error if it doesn't
    app_mod = import_module(app)
    try:
        imp.find_module(modname, app_mod.__path__ if hasattr(app_mod, '__path__') else None)
    except ImportError:
        # this ImportError will be due to the module not existing
        # so here we can silently ignore it.  But an ImportError
        # when we import_module() should not be ignored
        if failfast:
            raise
        elif verbose:
            print(u"Could not find %r from %r" % (modname, app)) # changed
            traceback.print_exc() # changed
        return None

    module = import_module(module_name)

    if verbose:
        print(u"Loaded %r from %r" % (modname, app))
    return module


def load(modname, verbose=False, failfast=False):
    """
    Loads all modules with name 'modname' from all installed apps.

    If verbose is True, debug information will be printed to stdout.

    If failfast is True, import errors will not be surpressed.
    """
    for app in installed_apps():
        get_module(app, modname, verbose, failfast)


def iterload(modname, verbose=False, failfast=False):
    """
    Loads all modules with name 'modname' from all installed apps and returns
    and iterator of those modules.

    If verbose is True, debug information will be printed to stdout.

    If failfast is True, import errors will not be surpressed.
    """
    return filter(None, (get_module(app, modname, verbose, failfast)
                         for app in installed_apps()))

def load_object(import_path):
    """
    Loads an object from an 'import_path', like in MIDDLEWARE_CLASSES and the
    likes.

    Import paths should be: "mypackage.mymodule.MyObject". It then imports the
    module up until the last dot and tries to get the attribute after that dot
    from the imported module.

    If the import path does not contain any dots, a TypeError is raised.

    If the module cannot be imported, an ImportError is raised.

    If the attribute does not exist in the module, a AttributeError is raised.
    """
    if '.' not in import_path:
        raise TypeError(
            "'import_path' argument to 'django_load.core.load_object' must "
            "contain at least one dot."
        )
    module_name, object_name = import_path.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, object_name)

def iterload_objects(import_paths):
    """
    Load a list of objects.
    """
    return map(load_object, import_paths)

def get_subclasses(c):
    """
    Get all subclasses of a given class
    """
    return c.__subclasses__() + sum(map(get_subclasses, c.__subclasses__()), [])

def load_from_file(module_path):
    """
    Load a python module from its absolute filesystem path
    """
    from imp import load_module, PY_SOURCE

    imported = None
    if module_path:
        with open(module_path, 'r') as openfile:
            imported = load_module("mod", openfile, module_path, ('imported', 'r', PY_SOURCE))
    return imported
