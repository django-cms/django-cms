# -*- coding: utf-8 -*-


TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'
REFRESH_PAGE = 'REFRESH_PAGE'
URL_CHANGE = 'URL_CHANGE'
RIGHT = object() # this is a trick so "foo is RIGHT" will only ever work for this, same goes for LEFT.
LEFT = object()

# Plugin actions
PLUGIN_MOVE_ACTION = 'move'
PLUGIN_COPY_ACTION = 'copy'
