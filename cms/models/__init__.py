from moderatormodels import *
from pagemodel import *
from permissionmodels import *
from pluginmodel import *
from titlemodels import *

from django.core.exceptions import ImproperlyConfigured
from cms import signals
from cms import plugin_pool

from django.conf import settings as d_settings
plugin_pool.plugin_pool.discover_plugins()

def validate_settings():
    if not "django.core.context_processors.request" in d_settings.TEMPLATE_CONTEXT_PROCESSORS:
        raise ImproperlyConfigured('django-cms needs django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')
    if not 'mptt' in d_settings.INSTALLED_APPS:
        raise ImproperlyConfigured('django-cms needs django-mptt installed.')
    
validate_settings()


def validate_dependencies():
    # check for right version of reversions
    if 'reversion' in d_settings.INSTALLED_APPS:
        from reversion.admin import VersionAdmin
        if not hasattr(VersionAdmin, 'get_urls'):
            raise ImproperlyConfigured('django-cms requires never version of reversion (VersionAdmin must contain get_urls method)')

validate_dependencies()
    