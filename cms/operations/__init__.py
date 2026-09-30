# Placeholder operations
ADD_PLUGIN = 'add_plugin'
CHANGE_PLUGIN = 'change_plugin'
DELETE_PLUGIN = 'delete_plugin'
MOVE_PLUGIN = 'move_plugin'
CUT_PLUGIN = 'cut_plugin'
PASTE_PLUGIN = 'paste_plugin'
PASTE_PLACEHOLDER = 'paste_placeholder'
ADD_PLUGINS_FROM_PLACEHOLDER = 'add_plugins_from_placeholder'
CLEAR_PLACEHOLDER = 'clear_placeholder'

# Page operations
CHANGE_PAGE = 'change_page'
ADD_PAGE = 'add_page'
CHANGE_PAGE_ADVANCED_SETTINGS = 'change_page_advanced_settings'
CHANGE_PAGE_PERMISSIONS = 'change_page_permissions'
CHANGE_GLOBAL_PAGE_PERMISSION = 'change_global_page_permission'
MOVE_PAGE = 'move_page'
DELETE_PAGE = 'delete_page'
SET_HOME = 'set_home'
COPY_PAGE = 'copy_page'
COPY_PAGE_FROM_SOURCE = 'copy_page_from_source'

# Page translation operations
ADD_PAGE_TRANSLATION = 'add_page_translation'
CHANGE_PAGE_TRANSLATION = 'change_page_translation'
DELETE_PAGE_TRANSLATION = 'delete_page_translation'
PUBLISH_PAGE_TRANSLATION = 'publish_page_translation'
REVERT_PAGE_TRANSLATION_TO_LIVE = 'revert_page_translation_to_live'
CHANGE_PAGE_TEMPLATE = 'change_page_template'
COPY_PAGE_LANGUAGE = 'copy_page_language'
TOGGLE_PAGE_IN_NAVIGATION = 'toggle_page_in_navigation'

# Static placeholder operations
PUBLISH_STATIC_PLACEHOLDER = 'publish_static_placeholder'

PAGE_OPERATIONS = [MOVE_PAGE, DELETE_PAGE, SET_HOME, COPY_PAGE]
PAGE_TRANSLATION_OPERATIONS = [
    DELETE_PAGE_TRANSLATION,
    PUBLISH_PAGE_TRANSLATION,
    REVERT_PAGE_TRANSLATION_TO_LIVE,
    CHANGE_PAGE_TEMPLATE,
    COPY_PAGE_LANGUAGE,
    TOGGLE_PAGE_IN_NAVIGATION,
]
STATIC_PLACEHOLDER_OPERATIONS = [PUBLISH_STATIC_PLACEHOLDER]
