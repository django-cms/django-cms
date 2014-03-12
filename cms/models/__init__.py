# -*- coding: utf-8 -*-
from django.conf import settings as d_settings
from .settingmodels import *  # nopyflakes
from .pagemodel import *  # nopyflakes
from .permissionmodels import *  # nopyflakes
from .placeholdermodel import *  # nopyflakes
from .pluginmodel import *  # nopyflakes
from .titlemodels import *  # nopyflakes
from .placeholderpluginmodel import *  # nopyflakes
from .static_placeholder import *  # nopyflakes

# must be last
from cms import signals as s_import  # nopyflakes


def validate_settings():
    if not "django.core.context_processors.request" in d_settings.TEMPLATE_CONTEXT_PROCESSORS:
        raise ImproperlyConfigured('django-cms needs django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')
    if not 'mptt' in d_settings.INSTALLED_APPS:
        raise ImproperlyConfigured('django-cms needs django-mptt installed.')
    if 'cms.middleware.multilingual.MultilingualURLMiddleware' in d_settings.MIDDLEWARE_CLASSES and 'django.middleware.locale.LocaleMiddleware' in d_settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('django-cms MultilingualURLMiddleware replaces django.middleware.locale.LocaleMiddleware! Please remove django.middleware.locale.LocaleMiddleware from your MIDDLEWARE_CLASSES settings.')


def validate_dependencies():
    # check for right version of reversions
    if 'reversion' in d_settings.INSTALLED_APPS:
        from reversion.admin import VersionAdmin
        if not hasattr(VersionAdmin, 'get_urls'):
            raise ImproperlyConfigured('django-cms requires never version of reversion (VersionAdmin must contain get_urls method)')

validate_dependencies()
validate_settings()
