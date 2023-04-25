
TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'
REFRESH_PAGE = 'REFRESH_PAGE'
FOLLOW_REDIRECT = 'FOLLOW_REDIRECT'
URL_CHANGE = 'URL_CHANGE'
RIGHT = object()  # this is a trick so "foo is RIGHT" will only ever work for this, same goes for LEFT.
LEFT = object()

PUBLISHER_STATE_DEFAULT = 0
PUBLISHER_STATE_DIRTY = 1
# Page was marked published, but some of page parents are not.
PUBLISHER_STATE_PENDING = 4

PAGE_TYPES_ID = "page_types"
PAGE_TREE_POSITIONS = ('last-child', 'first-child', 'left', 'right')

VISIBILITY_ALL = None
VISIBILITY_USERS = 1
VISIBILITY_ANONYMOUS = 2

X_FRAME_OPTIONS_INHERIT = 0
X_FRAME_OPTIONS_DENY = 1
X_FRAME_OPTIONS_SAMEORIGIN = 2
X_FRAME_OPTIONS_ALLOW = 3

PAGE_USERNAME_MAX_LENGTH = 255

SLUG_REGEXP = '[0-9A-Za-z-_.//]+'
NEGATE_SLUG_REGEXP = '[^0-9A-Za-z-_.//]+'

EXPIRE_NOW = 0
# HTTP Specification says max caching should only be up to one year.
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
