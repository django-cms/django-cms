VERSION = (2, 0, 0, 'alpha')
__version__ = '.'.join(map(str, VERSION))

import signals
import plugin_pool
plugin_pool.plugin_pool.discover_plugins()