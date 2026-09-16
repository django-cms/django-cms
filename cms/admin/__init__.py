"""Admin registration for the ``cms`` app, and the public name for its classes.

Django's ``admin.autodiscover()`` imports this module, so importing the admin
classes here is what registers them. It stays a permanent façade: third-party
packages -- djangocms-versioning most of all -- subclass these by their historic
paths, and those must keep resolving.

The implementations live with the container that owns them:

=============================== =========================================
``PlaceholderAdmin`` and the plugin endpoints
                                :mod:`cms.core.admin.placeholder`
``UserSettingsAdmin``           :mod:`cms.core.admin.settings`
``PageAdmin``, ``PageContentAdmin``, the page forms
                                :mod:`cms.pages.admin.page`, :mod:`cms.pages.admin.forms`
``PagePermissionInlineAdmin`` and friends
                                :mod:`cms.permissions.admin`
``PageUserAdmin``, ``PageUserGroupAdmin``
                                :mod:`cms.permissions.useradmin`
=============================== =========================================
"""

import cms.core.admin.placeholder  # noqa: F401
import cms.core.admin.settings  # noqa: F401
import cms.pages.admin.page  # noqa: F401
import cms.permissions.admin  # noqa: F401
import cms.permissions.useradmin  # noqa: F401

# Piggyback off admin.autodiscover() to discover cms plugins
from cms import plugin_pool

plugin_pool.plugin_pool.discover_plugins()
