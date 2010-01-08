# patch settings 
try:
    import settings_patch
    from django.conf import settings
    settings_patch.patch()
except ImportError:
    """
    This exception means that either the application is being built, or is
    otherwise installed improperly. Both make running patch_settings
    irrelevant.
    """
    pass