VERSION = (2, 0, 0, 'RC1')
__version__ = '.'.join(map(str, VERSION))

# patch settings 
from conf import patch_settings
patch_settings()

