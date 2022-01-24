import cms.admin.pageadmin
import cms.admin.permissionadmin
import cms.admin.settingsadmin
import cms.admin.static_placeholder  # nopyflakes
import cms.admin.useradmin
# Piggyback off admin.autodiscover() to discover cms plugins
from cms import plugin_pool

plugin_pool.plugin_pool.discover_plugins()
