from django.conf import settings
from django.utils.translation import get_language, activate
from shutil import rmtree as _rmtree
from tempfile import template, mkdtemp, _exists
import StringIO
import sys

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
        
    def __enter__(self):
        self.old = {}
        for key, value in self.overrides.items():
            self.old[key] = getattr(settings, key)
            setattr(settings, key, value)
        
    def __exit__(self, type, value, traceback):
        for key, value in self.old.items():
            setattr(settings, key, value)


class StdoutOverride(object):
    """
    This overrides Python's the standard output and redirrects it to a StringIO
    object, so that on can test the output of the program.
    
    example:
    lines = None
    with StdoutOverride() as buffer:
        # print stuff
        lines = buffer.getvalue()
    """
    def __enter__(self):
        self.buffer = StringIO.StringIO()
        sys.stdout = self.buffer
        return self.buffer
        
    def __exit__(self, type, value, traceback):
        self.buffer.close()
        # Revert the stdout to the real one
        sys.stdout = sys.__stdout__



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
        self.testcase.login_user(self.user)
        
    def __exit__(self, exc, value, tb):
        self.testcase.user = None
        self.testcase.client.logout()