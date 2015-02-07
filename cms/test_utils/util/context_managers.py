# -*- coding: utf-8 -*-
import sys
from contextlib import contextmanager
from shutil import rmtree as _rmtree
from tempfile import template, mkdtemp, _exists

from django.contrib.auth import get_user_model
from django.utils.six.moves import StringIO
from django.utils.translation import get_language, activate


class NULL:
    pass


class StdOverride(object):
    def __init__(self, std='out', buffer=None):
        self.std = std
        self.buffer = buffer or StringIO()

    def __enter__(self):
        setattr(sys, 'std%s' % self.std, self.buffer)
        return self.buffer

    def __exit__(self, type, value, traceback):
        setattr(sys, 'std%s' % self.std, getattr(sys, '__std%s__' % self.std))

class StdoutOverride(StdOverride):
    """
    This overrides Python's the standard output and redirects it to a StringIO
    object, so that on can test the output of the program.

    example:
    lines = None
    with StdoutOverride() as buffer:
        # print stuff
        lines = buffer.getvalue()
    """
    def __init__(self, buffer=None):
        super(StdoutOverride, self).__init__('out', buffer)


class LanguageOverride(object):
    def __init__(self, language):
        self.newlang = language

    def __enter__(self):
        self.oldlang = get_language()
        activate(self.newlang)

    def __exit__(self, type, value, traceback):
        activate(self.oldlang)


class TemporaryDirectory:
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everthing contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix=template, dir=None):
        self.name = mkdtemp(suffix, prefix, dir)

    def __enter__(self):
        return self.name

    def cleanup(self):
        if _exists(self.name):
            _rmtree(self.name)

    def __exit__(self, exc, value, tb):
        self.cleanup()


class UserLoginContext(object):
    def __init__(self, testcase, user):
        self.testcase = testcase
        self.user = user

    def __enter__(self):
        loginok = self.testcase.client.login(username=getattr(self.user, get_user_model().USERNAME_FIELD),
                                             password=getattr(self.user, get_user_model().USERNAME_FIELD))
        self.old_user = getattr(self.testcase, 'user', None)
        self.testcase.user = self.user
        self.testcase.assertTrue(loginok)

    def __exit__(self, exc, value, tb):
        self.testcase.user = self.old_user
        if not self.testcase.user:
            delattr(self.testcase, 'user')
        self.testcase.client.logout()


class ChangeModel(object):
    """
    Changes attributes on a model while within the context.

    These changes *ARE* saved to the database for the context!
    """
    def __init__(self, instance, **overrides):
        self.instance = instance
        self.overrides = overrides

    def __enter__(self):
        self.old = {}
        for key, value in self.overrides.items():
            self.old[key] = getattr(self.instance, key, NULL)
            setattr(self.instance, key, value)
        self.instance.save()

    def __exit__(self, exc, value, tb):
        for key in self.overrides.keys():
            old_value = self.old[key]
            if old_value is NULL:
                delattr(self.instance, key)
            else:
                setattr(self.instance, key, old_value)
        self.instance.save()


@contextmanager
def disable_logger(logger):
    old = logger.disabled
    logger.disabled = True
    yield
    logger.disabled = old
