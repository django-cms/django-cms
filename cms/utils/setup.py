from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def validate_dependencies():
    """
    Check for installed apps, their versions and configuration options
    """
    if 'mptt' not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured('django CMS requires django-mptt package.')

    if 'reversion' in settings.INSTALLED_APPS:
        from reversion.admin import VersionAdmin
        if not hasattr(VersionAdmin, 'get_urls'):
            raise ImproperlyConfigured('django CMS requires newer version of reversion (VersionAdmin must contain get_urls method)')


def validate_settings():
    """
    Check project settings file for required options
    """
    if 'django.core.context_processors.request' not in settings.TEMPLATE_CONTEXT_PROCESSORS:
        raise ImproperlyConfigured('django CMS requires django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')


def setup():
    """
    Gather all checks and validations
    """
    validate_dependencies()
    validate_settings()
