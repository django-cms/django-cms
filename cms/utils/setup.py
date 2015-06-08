from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cms.utils.compat import DJANGO_1_6, DJANGO_1_7
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
    if DJANGO_1_6:
        # While setup is called both in all the Django versions only 1.6-
        # requires paching the AppCache. 1.7 provides a cleaner way to handle
        # this in AppConfig and thus the patching is left for older version only
        from django.db.models import loading
        old_get_models = loading.AppCache.get_models

        def get_models_patched(self, **kwargs):
            ret_value = old_get_models(self, **kwargs)
            from cms.plugin_pool import plugin_pool
            plugin_pool.set_plugin_meta()
            return ret_value

        loading.AppCache.get_models = get_models_patched
    validate_dependencies()
    validate_settings()
