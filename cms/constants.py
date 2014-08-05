# -*- coding: utf-8 -*-


TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'
TEMPLATE_INHERITANCE_LABEL = 'Inherit the template of the nearest ancestor'
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
