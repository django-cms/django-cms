.. _toolbar-api-reference:

########
Toolbar
########

The toolbar can contain various items, some of which in turn can contain other items. These items
are represented by the classes listed in :mod:`cms.toolbar.items`, and created using the various
APIs described below.

..  admonition:: Do not instantiate these classes manually

    **These classes are described here for reference purposes only.** It is strongly recommended
    that you do not create instances yourself, but use the methods listed here.


*******************
Classes and methods
*******************

:ref:`Common parameters <toolbar_parameters>` (``key``, ``verbose_name``, ``position``,
``on_close``, ``disabled``, ``active``) and options are described at the end of this document.

..  module:: cms.toolbar.toolbar

..  autoclass:: CMSToolbar
    :members:
    :inherited-members:
    :show-inheritance:


..  module:: cms.toolbar.items

..  autoclass:: Menu
    :members:
    :inherited-members:
    :show-inheritance:

..  autoclass:: SubMenu
    :members:
    :inherited-members:
    :show-inheritance:


..  autoclass:: LinkItem
    :members:
    :show-inheritance:

..  autoclass:: SideframeItem
    :members:
    :show-inheritance:

..  autoclass:: ModalItem
    :members:
    :show-inheritance:

..  autoclass:: AjaxItem
    :members:
    :show-inheritance:

..  autoclass:: Break
    :members:
    :show-inheritance:

..  autoclass:: ButtonList
    :members:
    :show-inheritance:

..  autoclass:: Button
    :members:
    :show-inheritance:

..  autoclass:: SideframeButton
    :members:
    :show-inheritance:

..  autoclass:: ModalButton
    :members:
    :show-inheritance:

..  autoclass:: BaseItem
    :members:
    :show-inheritance:

..  autoclass:: ToolbarAPIMixin
    :members:

..  autoclass:: ItemSearchResult
    :members:
    :show-inheritance:

..  module:: cms.toolbar_base.CMSToolbar

..  autoclass:: ItemSearchResult
    :members:
    :show-inheritance:


.. _toolbar_parameters:

**********
Parameters
**********

The methods described below for creating/modifying toolbar items share a number of common
parameters:

..  option:: key

    a unique identifier (typically a string)

..  option:: verbose_name

    the displayed text in the item

..  option:: position

    The position index of the new item in the list of items. May be:

    #. ``None`` - appends the item to the list
    #. an integer - inserts the item at that index in the list
    #. an object already in the list - Inserts the item into the list immediately before the object;
       must be a sub-class of :class:`~cms.toolbar.items.BaseItem`, and must exist in the list
    #. an :class:`~cms.toolbar.items.ItemSearchResult` - inserts the item into the list immediately
       before the ``ItemSearchResult``. ``ItemSearchResult`` may be treated as an integer.

..  option:: on_close:

    Determines what happens after closing a frame (sideframe or modal) that has been opened by a
    menu item. May be:

    #. ``None`` - does nothing when the sideframe closes
    #. :const:`~cms.constants.REFRESH_PAGE` - refreshes the page when the frame closes
    #. a URL - opens the URLS when the frame is closed.

..  option:: disabled

    Greys out the item and renders it inoperable.

..  option::  active

    Applies to buttons only; renders the button it its 'activated' state.


..  option::  side

    Either :data:`cms.constants.LEFT` or :data:`cms.constants.RIGHT` (both
    unique objects denoted above as <object object>). Decides to which side
    of the toolbar the item should be added.


*************************************
django CMS constants used in toolbars
*************************************

..  module:: cms.constants
    :noindex:

..  autodata:: REFRESH_PAGE
   :no-value:

..  module:: cms.cms_toolbars

..  autodata:: ADMIN_MENU_IDENTIFIER
   :no-value:

..  autodata:: LANGUAGE_MENU_IDENTIFIER
   :no-value:

..  autodata:: PAGE_MENU_IDENTIFIER
   :no-value:
