VERSION = (2, 1, 0, 'alpha')
if VERSION[-1] != "final":
    __version__ = '.'.join(map(str, VERSION))
else:
    __version__ = '.'.join(map(str, VERSION[:-1]))


# patch settings 
try:
    from django.conf import settings
    if 'cms' in settings.INSTALLED_APPS:
        from conf import patch_settings
        patch_settings()
except ImportError:
    """
    This exception means that either the application is being built, or is
    otherwise installed improperly. Both make running patch_settings
    irrelevant.
    """
    pass

