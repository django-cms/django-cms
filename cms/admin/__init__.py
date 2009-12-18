import pageadmin
import useradmin
import permissionadmin

# Piggyback off admin.autodiscover() to discover cms plugins
from cms import plugin_pool
plugin_pool.plugin_pool.discover_plugins()
