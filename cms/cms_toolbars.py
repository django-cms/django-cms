"""django CMS' own toolbar registrations, and the public name for all of them.

This module is the ``cms`` app's toolbar autodiscovery entry point
(``autodiscover_modules("cms_toolbars")``), so importing the classes here is what
registers them. It stays a permanent façade rather than a deprecated shim: the
``CMS_TOOLBARS`` setting names these classes by dotted path, third-party code
imports the menu identifiers from here, and both must keep working.

The implementations live with the container that owns them:

=============================== =========================================
``PlaceholderToolbar``          :mod:`cms.core.editing.toolbar`
``BasicToolbar``, ``HelpToolbar``, ``AppearanceToolbar``
                                :mod:`cms.toolbar.chrome`
``PageToolbar``                 :mod:`cms.pages.toolbar`
=============================== =========================================
"""

from cms.core.editing.toolbar import PlaceholderToolbar
from cms.pages.toolbar import (
    ADD_PAGE_LANGUAGE_BREAK,
    COPY_PAGE_LANGUAGE_BREAK,
    HISTORY_MENU_BREAK,
    MANAGE_PAGES_BREAK,
    PAGE_MENU_ADD_IDENTIFIER,
    PAGE_MENU_FIRST_BREAK,
    PAGE_MENU_FOURTH_BREAK,
    PAGE_MENU_IDENTIFIER,
    PAGE_MENU_LAST_BREAK,
    PAGE_MENU_SECOND_BREAK,
    PAGE_MENU_THIRD_BREAK,
    REMOVE_PAGE_LANGUAGE_BREAK,
    TEMPLATE_MENU_BREAK,
    PageToolbar,
)
from cms.toolbar.chrome import (
    ADMIN_MENU_IDENTIFIER,
    ADMIN_SITES_BREAK,
    ADMINISTRATION_BREAK,
    CLIPBOARD_BREAK,
    DEFAULT_HELP_MENU_ITEMS,
    HELP_MENU_BREAK,
    HELP_MENU_IDENTIFIER,
    LANGUAGE_MENU_IDENTIFIER,
    SHORTCUTS_BREAK,
    TOOLBAR_DISABLE_BREAK,
    USER_SETTINGS_BREAK,
    AppearanceToolbar,
    BasicToolbar,
    HelpToolbar,
)

__all__ = [
    # toolbar container
    "ADMINISTRATION_BREAK",
    "ADMIN_MENU_IDENTIFIER",
    "ADMIN_SITES_BREAK",
    "AppearanceToolbar",
    "BasicToolbar",
    "CLIPBOARD_BREAK",
    "DEFAULT_HELP_MENU_ITEMS",
    "HELP_MENU_BREAK",
    "HELP_MENU_IDENTIFIER",
    "HelpToolbar",
    "LANGUAGE_MENU_IDENTIFIER",
    "SHORTCUTS_BREAK",
    "TOOLBAR_DISABLE_BREAK",
    "USER_SETTINGS_BREAK",
    # core container
    "PlaceholderToolbar",
    # pages container
    "ADD_PAGE_LANGUAGE_BREAK",
    "COPY_PAGE_LANGUAGE_BREAK",
    "HISTORY_MENU_BREAK",
    "MANAGE_PAGES_BREAK",
    "PAGE_MENU_ADD_IDENTIFIER",
    "PAGE_MENU_FIRST_BREAK",
    "PAGE_MENU_FOURTH_BREAK",
    "PAGE_MENU_IDENTIFIER",
    "PAGE_MENU_LAST_BREAK",
    "PAGE_MENU_SECOND_BREAK",
    "PAGE_MENU_THIRD_BREAK",
    "PageToolbar",
    "REMOVE_PAGE_LANGUAGE_BREAK",
    "TEMPLATE_MENU_BREAK",
]
