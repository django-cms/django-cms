from django.core.exceptions import ImproperlyConfigured
VERSION = (2, 0, 0, 'alpha')
__version__ = '.'.join(map(str, VERSION))

import signals
import plugin_pool

from django.conf import settings as d_settings
plugin_pool.plugin_pool.discover_plugins()

def validate_settings():
    if not "django.core.context_processors.request" in d_settings.TEMPLATE_CONTEXT_PROCESSORS:
        raise ImproperlyConfigured('django-cms needs django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')
    if not 'mptt' in d_settings.INSTALLED_APPS:
        raise ImproperlyConfigured('django-cms needs django-mptt installed.')
    
validate_settings()