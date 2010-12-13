'''
Created on Dec 10, 2010

@author: jonas
'''
from django.conf import settings

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