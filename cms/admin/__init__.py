import cms.admin.pageadmin  # noqa: F401
import cms.admin.permissionadmin  # noqa: F401
import cms.admin.placeholderadmin  # noqa: F401
import cms.admin.settingsadmin  # noqa: F401
import cms.admin.static_placeholder  # noqa: F401
import cms.admin.useradmin  # noqa: F401

# Piggyback off admin.autodiscover() to discover cms plugins
from cms import plugin_pool

plugin_pool.plugin_pool.discover_plugins()
