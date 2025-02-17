from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import engines
from django.template.backends.django import DjangoTemplates

from cms.app_registration import (
    autodiscover_cms_configs,
    backwards_compatibility_config,
    configure_cms_apps,
    get_cms_extension_apps,
    ready_cms_apps,
)
from cms.utils.compat.dj import is_installed as app_is_installed


def validate_dependencies():
    """
    Check for installed apps, their versions and configuration options
    """
    if not app_is_installed("treebeard"):
        raise ImproperlyConfigured(
            'django CMS requires django-treebeard. Please install it and add "treebeard" to INSTALLED_APPS.'
        )


def validate_settings():
    """
    Check project settings file for required options
    """
    django_engines = [engine for engine in engines.all() if isinstance(engine, DjangoTemplates)]

    if not django_engines:
        raise ImproperlyConfigured(
            "django CMS requires a template engine that inherits from "
            "'django.template.backends.django.DjangoTemplates'."
        )

    engine = django_engines[0]
    context_processors = engine.engine.context_processors
    template_request = "django.template.context_processors.request"

    if template_request not in context_processors:
        raise ImproperlyConfigured(
            "django CMS requires django.template.context_processors.request in "
            "'django.template.backends.django.DjangoTemplates' context processors."
        )


def setup():
    """
    Gather all checks and validations
    """
    from cms.plugin_pool import plugin_pool

    validate_dependencies()
    validate_settings()
    plugin_pool.validate_templates()


def setup_cms_apps():
    """
    Check for django apps which provide functionality that extends the
    cms. Configure all apps which have configs that declare use of
    any of this functionality.
    """
    autodiscover_cms_configs()
    cms_apps = get_cms_extension_apps()
    configure_cms_apps(cms_apps)
    backwards_compatibility_config()
    ready_cms_apps(cms_apps)
