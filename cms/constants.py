# -*- coding: utf-8 -*-

TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'
REFRESH_PAGE = 'REFRESH_PAGE'
URL_CHANGE = 'URL_CHANGE'
RIGHT = object() # this is a trick so "foo is RIGHT" will only ever work for this, same goes for LEFT.
LEFT = object()

# Plugin actions
PLUGIN_MOVE_ACTION = 'move'
PLUGIN_COPY_ACTION = 'copy'

PUBLISHER_STATE_DEFAULT = 0
PUBLISHER_STATE_DIRTY = 1
# Page was marked published, but some of page parents are not.
PUBLISHER_STATE_PENDING = 4

PAGE_TYPES_ID = "page_types"

VISIBILITY_ALL = None
VISIBILITY_USERS = 1
VISIBILITY_ANONYMOUS = 2

X_FRAME_OPTIONS_INHERIT = 0
X_FRAME_OPTIONS_DENY = 1
X_FRAME_OPTIONS_SAMEORIGIN = 2
X_FRAME_OPTIONS_ALLOW = 3

PAGE_USERNAME_MAX_LENGTH = 255

REVISION_INITIAL_COMMENT = "Initial version."

SLUG_REGEXP = '[0-9A-Za-z-_.//]+'

EXPIRE_NOW = 0
# HTTP Specification says max caching should only be up to one year.
MAX_EXPIRATION_TTL = 365 * 24 * 3600
