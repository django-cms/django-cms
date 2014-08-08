from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cms.utils.compat.dj import is_installed as app_is_installed


def validate_dependencies():
    """
    Check for installed apps, their versions and configuration options
    """
    if not app_is_installed('mptt'):
        raise ImproperlyConfigured('django CMS requires django-mptt package.')

    if not app_is_installed('reversion'):
        from reversion.admin import VersionAdmin
        if not hasattr(VersionAdmin, 'get_urls'):
            raise ImproperlyConfigured('django CMS requires newer version of reversion (VersionAdmin must contain get_urls method)')


def validate_settings():
    """
    Check project settings file for required options
    """
    if 'django.core.context_processors.request' not in settings.TEMPLATE_CONTEXT_PROCESSORS:
        raise ImproperlyConfigured('django CMS requires django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')

    multilingual_middleware = 'cms.middleware.multilingual.MultilingualURLMiddleware'
    locale_middleware =  'django.middleware.locale.LocaleMiddleware'

    if multilingual_middleware in settings.MIDDLEWARE_CLASSES and locale_middleware in settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('django CMS MultilingualURLMiddleware replaces django.middleware.locale.LocaleMiddleware! Please remove django.middleware.locale.LocaleMiddleware from your MIDDLEWARE_CLASSES settings.')


def setup():
    """
    Gather all checks and validations
    """
    validate_dependencies()
    validate_settings()
