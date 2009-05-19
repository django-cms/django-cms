from django.conf import settings

VERSION = (0, 1, 'pre')

if settings.DEBUG:
    from django.core.exceptions import ImproperlyConfigured
    # just check if Publisher is last application in INSTALLED_APPS
    print ">> checking"
    if not settings.INSTALLED_APPS[0] == "publisher.pre_publisher":
        raise ImproperlyConfigured("publisher.pre_publisher must be first installed application")
    if not settings.INSTALLED_APPS[-1] == "publisher.post_publisher":
        raise ImproperlyConfigured("publisher.post_publisher must be last installed application")