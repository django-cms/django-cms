from django.conf import settings
from models import Publisher, MpttPublisher
from mptt_support import Mptt
from manager import PublisherManager

__all__ = ('Publisher', 'PublisherManager', 'MpttPublisher', 'Mptt', 'VERSION')

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