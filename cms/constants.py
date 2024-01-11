"""
Collection of important constants used throughout django CMS.
"""


#: The token used to identify when a user selects "inherit" as template for a page.
TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'

REFRESH_PAGE = 'REFRESH_PAGE'
"""
Supplied to ``on_close`` arguments to refresh the current page when the frame is closed, for
example:

..  code-block:: python

    from cms.constants import REFRESH_PAGE

    self.toolbar.add_modal_item(
        'Modal item',
        url=modal_url,
        on_close=REFRESH_PAGE
        )
"""

FOLLOW_REDIRECT = 'FOLLOW_REDIRECT'
URL_CHANGE = 'URL_CHANGE'

#: Used as a position indicator in the toolbar: On the right side.
RIGHT = object()  # this is a trick so "foo is RIGHT" will only ever work for this, same goes for LEFT.

#: Used as a position indicator in the toolbar: On the left side.
LEFT = object()

PAGE_TYPES_ID = "page_types"
PAGE_TREE_POSITIONS = ('last-child', 'first-child', 'left', 'right')

#: Used for the ``limit_visibility_in_menu`` keyword argument to
#: :func: `create_page`.Does not limit menu visibility.
VISIBILITY_ALL = None

#: Used for the ``limit_visibility_in_menu`` keyword argument to :func: `create_page`.
#: Limits menu visibility to authenticated users.
VISIBILITY_USERS = 1

#: Used for the ``limit_visibility_in_menu`` keyword argument to :func: `create_page`.
#: Limits menu visibility to anonymous(not authenticated) users.
VISIBILITY_ANONYMOUS = 2

X_FRAME_OPTIONS_INHERIT = 0
X_FRAME_OPTIONS_DENY = 1
X_FRAME_OPTIONS_SAMEORIGIN = 2
X_FRAME_OPTIONS_ALLOW = 3

PAGE_USERNAME_MAX_LENGTH = 255

SLUG_REGEXP = '[0-9A-Za-z-_.//]+'

#: Used for cache control headers: 0 seconds, i.e. now.
EXPIRE_NOW = 0

#: Used for cache control headers: 365 * 24 * 3600 seconds, i.e. one year. HTTP specification says
#: max caching should only be up to one year.
MAX_EXPIRATION_TTL = 365 * 24 * 3600

PLUGIN_TOOLBAR_JS = "CMS._plugins.push([\"cms-plugin-%(pk)s\", %(config)s]);\n"

PLACEHOLDER_TOOLBAR_JS = "CMS._plugins.push([\"cms-placeholder-%(pk)s\", %(config)s]);"

# In the permissions system we use user levels to determine
# the depth in which the user has permissions.
# This constant represents a user that can see pages at all depths.
ROOT_USER_LEVEL = -1

GRANT_ALL_PERMISSIONS = 'All'

PUBLISH_COMMENT = "Publish"

SCRIPT_USERNAME = 'script'

CMS_CONFIG_NAME = 'cms_config'

MODAL_HTML_REDIRECT = '<body><a class="cms-view-new-object" target="_top" href="{url}">Redirecting...</a></body>'
