from django.conf import settings
from base import Publisher, Mptt

__all__ = ('Publisher', 'Mptt', 'VERSION')

VERSION = (0, 3, 'sintab')


'''
if settings.DEBUG:
    from django.core.exceptions import ImproperlyConfigured
    # just check if Publisher is last application in INSTALLED_APPS
    #if not settings.INSTALLED_APPS[0] == "publisher.pre_publisher":
    #    raise ImproperlyConfigured("publisher.pre_publisher must be first installed application")
    if not settings.INSTALLED_APPS[-1] == "publisher":
        raise ImproperlyConfigured("publisher must be last installed application")
    
'''