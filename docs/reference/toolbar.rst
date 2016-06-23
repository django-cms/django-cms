.. _toolbar-api-reference:

###########
The Toolbar
###########


All methods taking a ``side`` argument expect either
:data:`cms.constants.LEFT` or :data:`cms.constants.RIGHT` for that
argument.

Methods accepting the ``position`` argument can insert items at a specific
position. This can be either ``None`` to insert at the end, an integer
index at which to insert the item, a :class:`cms.toolbar.items.ItemSearchResult` to insert
it *before* that search result or a :class:`cms.toolbar.items.BaseItem` instance to insert
it *before* that item.


cms.toolbar.toolbar
===================

..  module:: cms.toolbar.toolbar

..  class:: CMSToolbar

    The toolbar class providing a Python API to manipulate the toolbar. Note
    that some internal attributes are not documented here.

    All methods taking a ``position`` argument expect either
    :data:`cms.constants.LEFT` or :data:`cms.constants.RIGHT` for that
    argument.

    This class inherits :class:`cms.toolbar.items.ToolbarMixin`, so please
    check that reference as well.

    .. attribute:: is_staff

        Whether the current user is a staff user or not.

    .. attribute:: edit_mode

        Whether the toolbar is in edit mode.

    .. attribute:: build_mode

        Whether the toolbar is in build mode.

    .. attribute:: show_toolbar

        Whether the toolbar should be shown or not.

    .. attribute:: csrf_token

        The CSRF token of this request

    .. attribute:: toolbar_language

        Language used by the toolbar.

    .. attribute:: watch_models

        A list of models this toolbar works on; used for redirection after editing
        (:ref:`url_changes`).

    .. method:: add_item(item, position=None)

        Low level API to add items.

        Adds an item, which must be an instance of
        :class:`cms.toolbar.items.BaseItem`, to the toolbar.

        This method should only be used for custom item classes, as all built-in
        item classes have higher level APIs.

        Read above for information on ``position``.

    .. method:: remove_item(item)

        Removes an item from the toolbar or raises a :exc:`KeyError` if it's
        not found.

    .. method:: get_or_create_menu(key. verbose_name, side=LEFT, position=None)

        If a menu with ``key`` already exists, this method will return that
        menu. Otherwise it will create a menu for that ``key`` with the given
        ``verbose_name`` on ``side`` at ``position`` and return it.


    ..  method:: get_menu(self, key, verbose_name=None, side=LEFT, position=None)

        If a menu with ``key`` already exists, this method will return that
        menu.


    .. method:: add_button(name, url, active=False, disabled=False, extra_classes=None, extra_wrapper_classes=None, side=LEFT, position=None)

        Adds a button to the toolbar. ``extra_wrapper_classes`` will be applied
        to the wrapping ``div`` while ``extra_classes`` are applied to the
        ``<a>``.

    .. method:: add_button_list(extra_classes=None, side=LEFT, position=None)

        Adds an (empty) button list to the toolbar and returns it. See
        :class:`cms.toolbar.items.ButtonList` for further information.



cms.toolbar.items
=================

.. important:: **Overlay** and **sideframe**

    Then django CMS *sideframe* has been replaced with an *overlay* mechanism. The API still refers
    to the ``sideframe``, because it is invoked in the same way, and what has changed is merely the
    behaviour in the user's browser.

    In other words, *sideframe* and the *overlay* refer to different versions of the same thing.

.. module:: cms.toolbar.items


.. class:: ItemSearchResult

    Used for the find APIs in :class:`ToolbarMixin`. Supports addition and
    subtraction of numbers. Can be cast to an integer.

    .. attribute:: item

        The item found.

    .. attribute:: index

        The index of the item.

.. class:: ToolbarMixin

    Provides APIs shared between :class:`cms.toolbar.toolbar.CMSToolbar` and
    :class:`Menu`.

    The ``active`` and ``disabled`` flags taken by all methods of this class
    specify the state of the item added.

    ``extra_classes`` should be either ``None`` or a list of class names as
    strings.

    .. attribute:: REFRESH_PAGE

        Constant to be used with ``on_close`` to refresh the current page when
        the frame is closed.

    .. attribute:: LEFT

        Constant to be used with ``side``.

    .. attribute:: RIGHT

        Constant to be used with ``side``.

    .. method:: get_item_count

        Returns the number of items in the toolbar or menu.

    ..  method:: get_alphabetical_insert_position(self, new_menu_name, item_type, default=0)

    .. method:: add_item(item, position=None)

        Low level API to add items, adds the ``item`` to the toolbar or menu
        and makes it searchable. ``item`` must be an instance of
        :class:`BaseItem`. Read above for information about the ``position``
        argument.

    .. method:: remove_item(item)

        Removes ``item`` from the toolbar or menu. If the item can't be found,
        a :exc:`KeyError` is raised.

    .. method:: find_items(item_type, **attributes)

        Returns a list of :class:`ItemSearchResult` objects matching all items
        of ``item_type``, which must be a sub-class of :class:`BaseItem`, where
        all attributes in ``attributes`` match.

    .. method:: find_first(item_type, **attributes)

        Returns the first :class:`ItemSearchResult` that matches the search or
        ``None``. The search strategy is the same as in :meth:`find_items`.
        Since positional insertion allows ``None``, it's safe to use the return
        value of this method as the position argument to insertion APIs.

    .. method:: add_sideframe_item(name, url, active=False, disabled=False, extra_classes=None, on_close=None, side=LEFT, position=None)

        Adds an item which opens ``url`` in the sideframe and returns it.

        ``on_close`` can be set to ``None`` to do nothing when the sideframe
        closes, :attr:`REFRESH_PAGE` to refresh the page when it
        closes or a URL to open once it closes.

    .. method:: add_modal_item(name, url, active=False, disabled=False, extra_classes=None, on_close=REFRESH_PAGE, side=LEFT, position=None)

        The same as :meth:`add_sideframe_item`, but opens the ``url`` in a
        modal dialog instead of the sideframe.

        ``on_close`` can be set to ``None`` to do nothing when the side modal
        closes, :attr:`REFRESH_PAGE` to refresh the page when it
        closes or a URL to open once it closes.

        Note: The default value for ``on_close`` is different in :meth:`add_sideframe_item` then in :meth:`add_modal_item`

    .. method:: add_link_item(name, url, active=False, disabled=False, extra_classes=None, side=LEFT, position=None)

        Adds an item that simply opens ``url`` and returns it.

    .. method:: add_ajax_item(name, action, active=False, disabled=False, extra_classes=None, data=None, question=None, side=LEFT, position=None)

        Adds an item which sends a POST request to ``action`` with ``data``.
        ``data`` should be ``None`` or a dictionary, the CSRF token will
        automatically be added to it.

        If ``question`` is set to a string, it will be asked before the
        request is sent to confirm the user wants to complete this action.


.. class:: BaseItem(position)

    Base item class.

    .. attribute:: template

        Must be set by sub-classes and point to a Django template

    .. attribute:: side

        Must be either :data:`cms.constants.LEFT` or
        :data:`cms.constants.RIGHT`.

    .. method:: render()

        Renders the item and returns it as a string. By default calls
        :meth:`get_context` and renders :attr:`template` with the context
        returned.

    .. method:: get_context()

        Returns the context (as dictionary) for this item.


.. class:: Menu(name, csrf_token, side=LEFT, position=None)

    The menu item class. Inherits :class:`ToolbarMixin` and provides the APIs
    documented on it.

    The ``csrf_token`` must be set as this class provides high level APIs to
    add items to it.

    .. method:: get_or_create_menu(key, verbose_name, side=LEFT, position=None)

        The same as :meth:`cms.toolbar.toolbar.CMSToolbar.get_or_create_menu` but adds
        the menu as a sub menu and returns a :class:`SubMenu`.

    .. method:: add_break(identifier=None, position=None)

        Adds a visual break in the menu, useful for grouping items, and
        returns it. ``identifier`` may be used to make this item searchable.


.. class:: SubMenu(name, csrf_token, side=LEFT, position=None)

    Same as :class:`Menu` but without the :meth:`Menu.get_or_create_menu` method.


.. class:: LinkItem(name, url, active=False, disabled=False, extra_classes=None, side=LEFT)

    Simple link item.


.. class:: SideframeItem(name, url, active=False, disabled=False, extra_classes=None, on_close=None, side=LEFT)

    Item that opens ``url`` in sideframe.


.. class:: AjaxItem(name, action, csrf_token, data=None, active=False, disabled=False, extra_classes=None, question=None, side=LEFT)

    An item which posts ``data`` to ``action``.


.. class:: ModalItem(name, url, active=False, disabled=False, extra_classes=None, on_close=None, side=LEFT)

    Item that opens ``url`` in the modal.


.. class:: Break(identifier=None)

    A visual break for menus. ``identifier`` may be provided to make this item
    searchable. Since breaks can only be within menus, they have no ``side``
    attribute.


.. class:: ButtonList(identifier=None, extra_classes=None, side=LEFT)

    A list of one or more buttons.

    The ``identifier`` may be provided to make this item searchable.

    .. method:: add_item(item)

        Adds ``item`` to the list of buttons. ``item`` must be an instance of
        :class:`Button`.

    .. method:: add_button(name, url, active=False, disabled=False, extra_classes=None)

        Adds a :class:`Button` to the list of buttons and returns it.


.. class:: Button(name, url, active=False, disabled=False, extra_classes=None)

    A button to be used with :class:`ButtonList`. Opens ``url`` when selected.


..  module:: cms.toolbar_pool

..  class:: ToolbarPool

    ..  method:: register(self, toolbar)

        Register this toolbar.


..  module:: cms.extensions.toolbar

..  class:: ExtensionToolbar

    ..  method:: get_page_extension_admin()

    ..  method:: _setup_extension_toolbar()

    ..  method:: get_title_extension_admin()
