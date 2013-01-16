# -*- coding: utf-8 -*-
__version__ = '2.4.0.beta'

# patch settings
try:
    from django.core.exceptions import ImproperlyConfigured
    try:
        from django.conf import settings
        if 'cms' in settings.INSTALLED_APPS:
            from conf import patch_settings
            patch_settings()
    except ImproperlyConfigured:
        """
        This exception means that either the application is being built, or is
        otherwise installed improperly. Both make running patch_settings
        irrelevant.
        """
        pass
except ImportError:  # pragma: no cover
    """
    This exception means that either the application is being built, or is
    otherwise installed improperly. Both make running patch_settings
    irrelevant.
    """
    pass
