VERSION = (2, 0, 0, 'RC3')
__version__ = '.'.join(map(str, VERSION))

# patch settings 
from conf import patch_settings
try:
    from django.conf import settings
    patch_settings()
except ImportError:
    """
    This exception means that either the application is being built, or is
    otherwise installed improperly. Both make running patch_settings
    irrelevant.
    """
    pass

