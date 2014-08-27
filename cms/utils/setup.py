from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cms.utils.compat.dj import is_installed as app_is_installed


def validate_dependencies():
    """
    Check for installed apps, their versions and configuration options
    """
    if not app_is_installed('mptt'):
        raise ImproperlyConfigured('django CMS requires django-mptt package.')

    if app_is_installed('reversion'):
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
    from django.db.models import loading

    def get_models_patched(app_mod=None, include_auto_created=False,
                           include_deferred=False, only_installed=True):
        loading.cache.get_models(app_mod, include_auto_created,
                                 include_deferred, only_installed)
        from cms.plugin_pool import plugin_pool
        plugin_pool.set_plugin_meta()

    loading.get_models = get_models_patched
    validate_dependencies()
    validate_settings()
