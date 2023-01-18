import warnings

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cms.utils.compat.dj import is_installed as app_is_installed


def validate_dependencies():
    """
    Check for installed apps, their versions and configuration options
    """
    if not app_is_installed('treebeard'):
        raise ImproperlyConfigured(
            'django CMS requires django-treebeard. Please install it and add "treebeard" to INSTALLED_APPS.'
        )


def validate_settings():
    """
    Check project settings file for required options
    """
    try:
        django_backend = [x for x in settings.TEMPLATES
                          if x['BACKEND'] == 'django.template.backends.django.DjangoTemplates'][0]
    except IndexError:
        raise ImproperlyConfigured(
            "django CMS requires django.template.context_processors.request in "
            "'django.template.backends.django.DjangoTemplates' context processors."
        )

    context_processors = django_backend.get('OPTIONS', {}).get('context_processors', [])
    if ('django.core.context_processors.request' not in context_processors and  # noqa: W504
            'django.template.context_processors.request' not in context_processors):
        raise ImproperlyConfigured("django CMS requires django.template.context_processors.request in "
                                   "'django.template.backends.django.DjangoTemplates' context processors.")

    if (
        hasattr(settings, "SEND_BROKEN_LINK_EMAILS") and  # noqa: W504
        "django.middleware.common.BrokenLinkEmailsMiddleware" not in getattr(settings, "MIDDLEWARE", [])
    ):
        warnings.warn('The setting "SEND_BROKEN_LINK_EMAILS" will not be honored by django CMS as of version 4.1. '
                      'Add "django.middleware.common.BrokenLinkEmailsMiddleware" to your MIDDLEWARE settings '
                      'instead.', DeprecationWarning)


def setup():
    """
    Gather all checks and validations
    """
    from cms.plugin_pool import plugin_pool
    validate_dependencies()
    validate_settings()
    plugin_pool.validate_templates()
