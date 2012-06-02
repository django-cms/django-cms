# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.signals import request_started
from django.db import reset_queries
from django.template import context
from django.utils.translation import get_language, activate
from shutil import rmtree as _rmtree
from tempfile import template, mkdtemp, _exists
import StringIO
import sys

class NULL:
    pass

class SettingsOverride(object):
    """
    Overrides Django settings within a context and resets them to their inital
    values on exit.
    
    Example:
    
        with SettingsOverride(DEBUG=True):
            # do something
    """
    
    def __init__(self, **overrides):
        self.overrides = overrides
        self.special_handlers = {
            'TEMPLATE_CONTEXT_PROCESSORS': self.template_context_processors,
        }
        
    def __enter__(self):
        self.old = {}
        for key, value in self.overrides.items():
            self.old[key] = getattr(settings, key, NULL)
            setattr(settings, key, value)
        
    def __exit__(self, type, value, traceback):
        for key, value in self.old.items():
            if value is not NULL:
                setattr(settings, key, value)
            else:
                delattr(settings,key) # do not pollute the context!
            self.special_handlers.get(key, lambda:None)()
    
    def template_context_processors(self):
        context._standard_context_processors = None


class StdOverride(object):
    def __init__(self, std='out', buffer=None):
        self.std = std
        self.buffer = buffer or StringIO.StringIO()
        
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
        loginok = self.testcase.client.login(username=self.user.username, 
                                             password=self.user.username)
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

class _AssertNumQueriesContext(object):
    def __init__(self, test_case, num, connection):
        self.test_case = test_case
        self.num = num
        self.connection = connection

    def __enter__(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.starting_queries = len(self.connection.queries)
        request_started.disconnect(reset_queries)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        settings.DEBUG = self.old_debug
        request_started.connect(reset_queries)
        if exc_type is not None:
            return

        final_queries = len(self.connection.queries)
        executed = final_queries - self.starting_queries
        
        queries = '\n'.join([q['sql'] for q in self.connection.queries[self.starting_queries:]])

        self.test_case.assertEqual(
            executed, self.num, "%d queries executed, %d expected. Queries executed:\n%s" % (
                executed, self.num, queries
            )
        )