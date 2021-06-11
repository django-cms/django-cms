.. _toolbar-api-reference:

###########
The Toolbar
###########

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

..  class:: CMSToolbar

    The toolbar is an instance of the ``cms.toolbar.toolbar.CMSToolbar`` class. This should not be
    confused with the :class:`~cms.toolbar_base.CMSToolbar`, the base class for *toolbar modifier
    classes* in other applications, that add items to and otherwise manipulates the toolbar.

    It is strongly recommended that you **only** interact with the toolbar in your own code via:

    * the APIs documented here
    * toolbar modifier classes based on ``cms.toolbar_base.CMSToolbar``

    You will notice that some of the methods documented here do not include some arguments present
    in the code. This is the *public* reference documentation, while the code may be subject to
    change without warning.

    Several of the following methods to create and add objects other objects to the toolbar are
    inherited from :class:`~cms.toolbar.items.ToolbarAPIMixin`.

    ..  method:: add_link_item

        See :meth:`ToolbarAPIMixin.add_link_item
        <cms.toolbar.items.ToolbarAPIMixin.add_link_item>`

    ..  method:: add_sideframe_item

        See :meth:`ToolbarAPIMixin.add_sideframe_item
        <cms.toolbar.items.ToolbarAPIMixin.add_sideframe_item>`

    ..  method:: add_modal_item

        See :meth:`ToolbarAPIMixin.add_modal_item
        <cms.toolbar.items.ToolbarAPIMixin.add_modal_item>`

    ..  method:: add_ajax_item

        See :meth:`ToolbarAPIMixin.add_ajax_item
        <cms.toolbar.items.ToolbarAPIMixin.add_ajax_item>`

    ..  method:: add_item

        See :meth:`ToolbarAPIMixin.add_item
        <cms.toolbar.items.ToolbarAPIMixin.add_item>`

    ..  method:: get_or_create_menu(key, verbose_name, position=None, disabled=False)

        If a :class:`~cms.toolbar.items.Menu` with :option:`key` already exists, this method will
        return that menu. Otherwise it will create a menu with the ``key`` identifier.

    ..  method:: get_menu(key)

        Will return the ``Menu`` identified with :option:`key`, or ``None``.

    ..  method:: add_button(name, url, active=False, disabled=False, position=None)

        Adds a :class:`~cms.toolbar.items.Button` to the toolbar.

    ..  method:: add_sideframe_button(name, url, active=False, disabled=False, on_close=None)

        Adds a :class:`~cms.toolbar.items.SideframeButton` to the toolbar.

    ..  method:: add_modal_button(name, url, active=False, disabled=False, on_close=REFRESH_PAGE)

        Adds a :class:`~cms.toolbar.items.ModalButton` to the toolbar.

    ..  method:: add_button_list(position=None)

        Adds an (empty) :class:`~cms.toolbar.items.ButtonList` to the toolbar and returns it.

    ..  method:: edit_mode_active

        Property; returns ``True`` if the content or structure board editing modes are active.

    ..  method:: watch_models

        Property; a list of models that the toolbar :ref:`watches for URL changes <url_changes>`,
        so it can redirect to the new URL on saving.


..  module:: cms.toolbar.items

..  class:: Menu

    Provides a menu in the toolbar. Use a :meth:`CMSToolbar.get_or_create_menu
    <cms.toolbar.toolbar.CMSToolbar.get_or_create_menu>` method to create a ``Menu`` instance. Can
    be added to :class:`~cms.toolbar.toolbar.CMSToolbar`.

    Inherits from :class:`SubMenu` below, so shares all of its methods, but in addition has:

    ..  method:: get_or_create_menu(key, verbose_name, disabled=False, position=None)

        Adds a new sub-menu, at :option:`position`, and returns a :class:`SubMenu`.


..  class:: SubMenu

    A child of a :class:`Menu`. Use a :meth:`Menu.get_or_create_menu
    <cms.toolbar.items.Menu.get_or_create_menu>` method to create a ``SubMenu`` instance. Can be
    added to ``Menu``.

    Several of the following methods to create and add objects are inherited from
    :class:`~cms.toolbar.items.ToolbarAPIMixin`.

    ..  method:: add_link_item

        See :meth:`ToolbarAPIMixin.add_link_item
        <cms.toolbar.items.ToolbarAPIMixin.add_link_item>`

    ..  method:: add_sideframe_item

        See :meth:`ToolbarAPIMixin.add_sideframe_item
        <cms.toolbar.items.ToolbarAPIMixin.add_sideframe_item>`

    ..  method:: add_modal_item

        See :meth:`ToolbarAPIMixin.add_modal_item
        <cms.toolbar.items.ToolbarAPIMixin.add_modal_item>`

    ..  method:: add_ajax_item

        See :meth:`ToolbarAPIMixin.add_ajax_item
        <cms.toolbar.items.ToolbarAPIMixin.add_ajax_item>`

    ..  method:: add_item

        See :meth:`ToolbarAPIMixin.add_item
        <cms.toolbar.items.ToolbarAPIMixin.add_item>`

    ..  method:: get_item_count

        Returns the number of items in the menu.

    Other methods:

    ..  method:: add_break(identifier=None, position=None)

        Adds a visual break in the menu, at :option:`position`, and returns it. ``identifier`` may
        be used to make this item searchable.


..  class:: LinkItem

    Sends a GET request. Use an :class:`~ToolbarAPIMixin.add_link_item` method to create a
    ``LinkItem`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`,
    :class:`~cms.toolbar.items.Menu`, :class:`~cms.toolbar.items.SubMenu`.

..  class:: SideframeItem

    Sends a GET request; loads response in a sideframe. Use an
    :class:`~ToolbarAPIMixin.add_sideframe_item` method to create a ``SideframeItem`` instance. Can
    be added to :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.Menu`,
    :class:`~cms.toolbar.items.SubMenu`.

..  class:: ModalItem

    Sends a GET request; loads response in a modal window. Use an
    :class:`~ToolbarAPIMixin.add_modal_item` method to create a ``ModalItem`` instance. Can be
    added to :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.Menu`,
    :class:`~cms.toolbar.items.SubMenu`.

..  class:: AjaxItem

    Sends a POST request. Use an :class:`~ToolbarAPIMixin.add_ajax_item` method to create a
    ``AjaxItem`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`,
    :class:`~cms.toolbar.items.Menu`, :class:`~cms.toolbar.items.SubMenu`.

..  class:: Break

    A visual break in a menu. Use an :class:`~cms.toolbar.items.SubMenu.add_break` method to create
    a ``Break`` instance. Can be added to :class:`~cms.toolbar.items.Menu`,
    :class:`~cms.toolbar.items.SubMenu`.

..  class:: ButtonList

    A visually-connected list of one or more buttons. Use an
    :meth:`~cms.toolbar.toolbar.CMSToolbar.add_button_list` method to create a ``Button`` instance.
    Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`.

    ..  method:: add_button(name, url, active=False, disabled=False)

        Adds a :class:`Button` to the list of buttons and returns it.

    ..  method:: add_sideframe_button(name, url, active=False, disabled=False, on_close=None)

        Adds a :class:`~cms.toolbar.items.ModalButton` to the toolbar.

    ..  method:: add_modal_button(name, url, active=False, disabled=False, on_close=REFRESH_PAGE)

        Adds an (empty) :class:`~cms.toolbar.items.ButtonList` to the toolbar and returns it.

    ..  method:: get_buttons

..  class:: Button

    Sends a GET request. Use a :meth:`CMSToolbar.add_button
    <cms.toolbar.toolbar.CMSToolbar.add_button>` or :meth:`ButtonList.add_button` method to create
    a ``Button`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`,
    :class:`~cms.toolbar.items.ButtonList`.

..  class:: SideframeButton

    Sends a GET request. Use a :meth:`CMSToolbar.add_sideframe_button
    <cms.toolbar.toolbar.CMSToolbar.add_sideframe_button>` or
    :meth:`ButtonList.add_sideframe_button` method to create a ``SideframeButton`` instance. Can be
    added to :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.ButtonList`.

..  class:: ModalButton

    Sends a GET request. Use a :meth:`CMSToolbar.add_modal_button
    <cms.toolbar.toolbar.CMSToolbar.add_modal_button>` or :meth:`ButtonList.add_modal_button`
    method to create a ``ModalButton`` instance. Can be added to
    :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.ButtonList`.

..  class:: BaseItem

    All toolbar items inherit from ``BaseItem``. If you need to create a custom toolbar item,
    sub-class ``BaseItem``.

    .. attribute:: template

        Must be set by sub-classes and point to a Django template

    .. method:: render()

        Renders the item and returns it as a string. By default calls
        :meth:`get_context` and renders :attr:`template` with the context
        returned.

    .. method:: get_context()

        Returns the context (as dictionary) for this item.


..  class:: ToolbarAPIMixin

    Provides APIs used by :class:`~cms.toolbar.toolbar.CMSToolbar` and :class:`Menu`.

    ..  method:: add_link_item(name, url, active=False, disabled=False, position=None)

        Adds a :class:`LinkItem` that opens ``url``, and returns it.

    ..  method:: add_sideframe_item(name, url, active=False, disabled=False, on_close=None, position=None)

        Adds a :class:`SideframeItem` that opens ``url`` in the sideframe and returns it.

    ..  method:: add_modal_item(name, url, active=False, disabled=False, on_close=REFRESH_PAGE, position=None)

        Similar to :meth:`add_sideframe_item`, but adds a :class:`ModalItem` that opens opens the
        ``url`` in a modal dialog instead of the sideframe, and returns it.

    ..  method:: add_ajax_item(name, action, active=False, disabled=False, \
                     data=None, question=None, position=None)

        Adds :class:`AjaxItem` that sends a POST request to ``action`` with ``data``, and returns
        it. ``data`` should be ``None`` or a dictionary. The CSRF token will automatically be added
        to the item.

        If a string is provided for ``question``, it will be presented to the user to allow
        confirmation before the request is sent.

    ..  method:: add_item(item, position=None)

        Adds an item (which must be a sub-class of :class:`~cms.toolbar.items.BaseItem`), and
        returns it. This is a low-level API, and you should always use one of the built-in
        object-specific methods to add items in preference if possible, using this method **only**
        for custom item classes.

    ..  method:: find_items(item_type)

        Returns a list of :class:`ItemSearchResult` objects matching all items of ``item_type``
        (e.g. ``LinkItem``).

    ..  method:: find_first(item_type, **attributes)

        Returns the first :class:`ItemSearchResult` that matches the search, or ``None``. The
        search strategy is the same as in :meth:`find_items`. The return value of this method is
        safe to use as the :option:`position` argument of the various APIs to add items.


..  class:: ItemSearchResult

    Returned by the find APIs in :class:`ToolbarAPIMixin`.

    An ``ItemSearchResult`` will have two useful attributes:

    .. attribute:: item

        The item found.

    .. attribute:: index

        The index of the item (its position amongst the other items).

    The ``ItemSearchResult`` itself can be cast to an integer, and supports addition and
    subtraction of numbers. See the :option:`position` parameter for more details, and
    :ref:`toolbar_control_item_position` for examples.


..  module:: cms.toolbar_base.CMSToolbar

..  class:: CMSToolbar

    The base class for toolbar modifiers.

    See :ref:`toolbar_how_to` for more information.


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

    * ``None`` - appends the item to the list
    * an integer - inserts the item at that index in the list
    * an object already in the list - Inserts the item into the list immediately before the object;
      must be a sub-class of :class:`~cms.toolbar.items.BaseItem`, and must exist in the list
    * an :class:`~cms.toolbar.items.ItemSearchResult` - inserts the item into the list immediately
      before the ``ItemSearchResult``. ``ItemSearchResult`` may be treated as an integer.

..  option:: on_close:

    Determines what happens after closing a frame (sideframe or modal) that has been opened by a
    menu item. May be:

    * ``None`` - does nothing when the sideframe closes
    * :const:`~cms.constants.REFRESH_PAGE` - refreshes the page when the frame closes
    * a URL - opens the URLS when the frame is closed.

..  option:: disabled

    Greys out the item and renders it inoperable.

..  option::  active

    Applies to buttons only; renders the button it its 'activated' state.


*************************************
django CMS constants used in toolbars
*************************************

..  module:: cms.constants
    :noindex:

..  data:: REFRESH_PAGE

    Supplied to ``on_close`` arguments to refresh the current page when the frame is closed, for
    example:

    ..  code-block:: python

        from cms.constants import REFRESH_PAGE

        self.toolbar.add_modal_item(
            'Modal item',
            url=modal_url,
            on_close=REFRESH_PAGE
            )


..  module:: cms.cms_toolbars

..  data:: ADMIN_MENU_IDENTIFIER

    The *Site* menu (that usually shows the project's domain name, *example.com* by default).
    ``ADMIN_MENU_IDENTIFIER`` allows you to get hold of this object easily. See
    :ref:`finding_toolbar_items` for an example of usage.

