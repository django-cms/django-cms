from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cms.utils.compat import DJANGO_1_7
from cms.utils.compat.dj import is_installed as app_is_installed


def validate_dependencies():
    """
    Check for installed apps, their versions and configuration options
    """
    if not app_is_installed('treebeard'):
        raise ImproperlyConfigured('django CMS requires django-treebeard. Please install it and add "treebeard" to INSTALLED_APPS.')

    if app_is_installed('reversion'):
        from reversion.admin import VersionAdmin
        if not hasattr(VersionAdmin, 'get_urls'):
            raise ImproperlyConfigured('django CMS requires newer version of reversion (VersionAdmin must contain get_urls method)')


def validate_settings():
    """
    Check project settings file for required options
    """
    if DJANGO_1_7:
        if 'django.core.context_processors.request' not in settings.TEMPLATE_CONTEXT_PROCESSORS:
            raise ImproperlyConfigured('django CMS requires django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')
    else:
        try:
            django_backend = [x for x in settings.TEMPLATES
                              if x['BACKEND'] == 'django.template.backends.django.DjangoTemplates'][0]
        except IndexError:
            raise ImproperlyConfigured("django CMS requires django.template.context_processors.request in "
                                       "'django.template.backends.django.DjangoTemplates' context processors.")

        context_processors = django_backend.get('OPTIONS', {}).get('context_processors', [])
        if ('django.core.context_processors.request' not in context_processors and
                'django.template.context_processors.request' not in context_processors):
            raise ImproperlyConfigured("django CMS requires django.template.context_processors.request in "
                                       "'django.template.backends.django.DjangoTemplates' context processors.")


def setup():
    """
    Gather all checks and validations
    """
    validate_dependencies()
    validate_settings()
