##############
API References
##############

*******
cms.api
*******

Python APIs for creating CMS content. This is done in :mod:`cms.api` and not
on the models and managers, because the direct API via models and managers is
slightly counterintuitive for developers. Also the functions defined in this
module do sanity checks on arguments.

.. warning:: None of the functions in this module does any security or permission
             checks. They verify their input values to be sane wherever
             possible, however permission checks should be implemented manually
             before calling any of these functions.

.. warning:: Due to potential circular dependency issues, it's recommended
             to import the api in the functions that uses its function.

             e.g. use:

             ::

                 def my_function():
                     from cms.api import api_function

                     api_function(...)

             instead of:

             ::

                 from cms.api import api_function

                 def my_function():
                     api_function(...)


Functions and constants
=======================

.. module:: cms.api

.. data:: VISIBILITY_ALL

    Used for the ``limit_menu_visibility`` keyword argument to
    :func:`create_page`. Does not limit menu visibility.


.. data:: VISIBILITY_USERS

    Used for the ``limit_menu_visibility`` keyword argument to
    :func:`create_page`. Limits menu visibility to authenticated users.

.. data:: VISIBILITY_ANONYMOUS

    Used for the ``limit_menu_visibility`` keyword argument to
    :func:`create_page`. Limits menu visibility to anonymous (not authenticated) users.


.. function:: create_page(title, template, language, menu_title=None, slug=None, apphook=None, apphook_namespace=None, redirect=None, meta_description=None, created_by='python-api', parent=None, publication_date=None, publication_end_date=None, in_navigation=False, soft_root=False, reverse_id=None, navigation_extenders=None, published=False, site=None, login_required=False, limit_visibility_in_menu=VISIBILITY_ALL, position="last-child", overwrite_url=None, xframe_options=Page.X_FRAME_OPTIONS_INHERIT, with_revision=False)

    Creates a :class:`cms.models.pagemodel.Page` instance and returns it. Also
    creates a :class:`cms.models.titlemodels.Title` instance for the specified
    language.

    :param string title: Title of the page
    :param string template: Template to use for this page. Must be in :setting:`CMS_TEMPLATES`
    :param string language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param string menu_title: Menu title for this page
    :param string slug: Slug for the page, by default uses a slugified version of *title*
    :param apphook: Application to hook on this page, must be a valid apphook
    :type apphook: string or :class:`cms.app_base.CMSApp` sub-class
    :param string apphook_namespace: Name of the apphook namespace
    :param string redirect: URL redirect
    :param string meta_description: Description of this page for SEO
    :param created_by: User that is creating this page
    :type created_by: string of :class:`django.contrib.auth.models.User` instance
    :param parent: Parent page of this page
    :type parent: :class:`cms.models.pagemodel.Page` instance
    :param datetime publication_date: Date to publish this page
    :param datetime publication_end_date: Date to unpublish this page
    :param bool in_navigation: Whether this page should be in the navigation or not
    :param bool soft_root: Whether this page is a soft root or not
    :param string reverse_id: Reverse ID of this page (for template tags)
    :param string navigation_extenders: Menu to attach to this page. Must be a valid menu
    :param bool published: Whether this page should be published or not
    :param site: Site to put this page on
    :type site: :class:`django.contrib.sites.models.Site` instance
    :param bool login_required: Whether users must be logged in or not to view this page
    :param limit_menu_visibility: Limits visibility of this page in the menu
    :type limit_menu_visibility: :data:`VISIBILITY_ALL` or :data:`VISIBILITY_USERS` or :data:`VISIBILITY_ANONYMOUS`
    :param string position: Where to insert this node if *parent* is given, must be ``'first-child'`` or ``'last-child'``
    :param string overwrite_url: Overwritten path for this page
    :param integer xframe_options: X Frame Option value for Clickjacking protection
    :param bool with_revision: Whether to create a revision for the new page.


.. function:: create_title(language, title, page, menu_title=None, slug=None, redirect=None, meta_description=None, parent=None, overwrite_url=None, with_revision=False)

    Creates a :class:`cms.models.titlemodels.Title` instance and returns it.

    :param string language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param string title: Title of the page
    :param page: The page for which to create this title
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param string menu_title: Menu title for this page
    :param string slug: Slug for the page, by default uses a slugified version of *title*
    :param string redirect: URL redirect
    :param string meta_description: Description of this page for SEO
    :param parent: Used for automated slug generation
    :type parent: :class:`cms.models.pagemodel.Page` instance
    :param string overwrite_url: Overwritten path for this page
    :param bool with_revision: Whether to create a revision for the new page.


.. function:: add_plugin(placeholder, plugin_type, language, position='last-child', target=None,  **data)

    Adds a plugin to a placeholder and returns it.

    :param placeholder: Placeholder to add the plugin to
    :type placeholder: :class:`cms.models.placeholdermodel.Placeholder` instance
    :param plugin_type: What type of plugin to add
    :type plugin_type: string or :class:`cms.plugin_base.CMSPluginBase` sub-class, must be a valid plugin
    :param string language: Language code for this plugin, must be in :setting:`django:LANGUAGES`
    :param string position: Position to add this plugin to the placeholder, must be a valid django-mptt position
    :param target: Parent plugin. Must be plugin instance
    :param kwargs data: Data for the plugin type instance


.. function:: create_page_user(created_by, user, can_add_page=True, can_change_page=True, can_delete_page=True, can_recover_page=True, can_add_pageuser=True, can_change_pageuser=True, can_delete_pageuser=True, can_add_pagepermission=True, can_change_pagepermission=True, can_delete_pagepermission=True, grant_all=False)

    Creates a page user for the user provided and returns that page user.

    :param created_by: The user that creates the page user
    :type created_by: :class:`django.contrib.auth.models.User` instance
    :param user: The user to create the page user from
    :type user: :class:`django.contrib.auth.models.User` instance
    :param bool can_*: Permissions to give the user
    :param bool grant_all: Grant all permissions to the user


.. function:: assign_user_to_page(page, user, grant_on=ACCESS_PAGE_AND_DESCENDANTS, can_add=False, can_change=False, can_delete=False, can_change_advanced_settings=False, can_publish=False, can_change_permissions=False, can_move_page=False, grant_all=False)

    Assigns a user to a page and gives them some permissions. Returns the
    :class:`cms.models.permissionmodels.PagePermission` object that gets
    created.

    :param page: The page to assign the user to
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param user: The user to assign to the page
    :type user: :class:`django.contrib.auth.models.User` instance
    :param grant_on: Controls which pages are affected
    :type grant_on: :data:`cms.models.permissionmodels.ACCESS_PAGE`, :data:`cms.models.permissionmodels.ACCESS_CHILDREN`, :data:`cms.models.permissionmodels.ACCESS_DESCENDANTS` or :data:`cms.models.permissionmodels.ACCESS_PAGE_AND_DESCENDANTS`
    :param can_*: Permissions to grant
    :param bool grant_all: Grant all permissions to the user


.. function:: publish_page(page, user, language)

    Publishes a page.

    :param page: The page to publish
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param user: The user that performs this action
    :type user: :class:`django.contrib.auth.models.User` instance
    :param string language: The target language to publish to

.. function:: publish_pages(include_unpublished=False, language=None, site=None)

    Publishes multiple pages defined by parameters.

    :param bool include_unpublished: Set to ``True`` to publish all drafts, including unpublished ones; otherwise, only already published pages will be republished
    :param string language: If given, only pages in this language will be published; otherwise, all languages will be published
    :param site: Specify a site to publish pages for specified site only; if not specified pages from all sites are published
    :type site: :class:`django.contrib.sites.models.Site` instance

.. function:: get_page_draft(page):

    Returns the draft version of a page, regardless if the passed in
    page is a published version or a draft version.

    :param page: The page to get the draft version
    :type page: :class:`cms.models.pagemodel.Page` instance
    :return page: draft version of the page

.. function:: copy_plugins_to_language(page, source_language, target_language, only_empty=True):

    Copy the plugins to another language in the same page for all the page
    placeholders.

    By default plugins are copied only if placeholder has no plugin for the target language; use ``only_empty=False`` to change this.

    .. warning:: This function skips permissions checks

    :param page: the page to copy
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param string source_language: The source language code, must be in :setting:`django:LANGUAGES`
    :param string target_language: The source language code, must be in :setting:`django:LANGUAGES`
    :param bool only_empty: if False, plugin are copied even if plugins exists in the
     target language (on a placeholder basis).
    :return int: number of copied plugins

Example workflows
=================

Create a page called ``'My Page`` using the template ``'my_template.html'`` and
add a text plugin with the content ``'hello world'``. This is done in English::

    from cms.api import create_page, add_plugin

    page = create_page('My Page', 'my_template.html', 'en')
    placeholder = page.placeholders.get(slot='body')
    add_plugin(placeholder, 'TextPlugin', 'en', body='hello world')


*************
cms.constants
*************

.. module:: cms.constants

.. data:: TEMPLATE_INHERITANCE_MAGIC

    The token used to identify when a user selects "inherit" as template for a
    page.

.. data:: LEFT

    Used as a position indicator in the toolbar.

.. data:: RIGHT

    Used as a position indicator in the toolbar.

.. data:: REFRESH

    Constant used by the toolbar.

.. data:: EXPIRE_NOW

    Constant of 0 (zero) used for cache control headers

.. data:: MAX_EXPIRATION_TTL

    Constant of 31536000 or 365 days in seconds used for cache control headers

************
cms.app_base
************

.. module:: cms.app_base

.. autoclass:: CMSApp

    .. attribute:: _urls

        list of urlconfs: example: ``_urls = ["myapp.urls"]``

    .. attribute:: _menus = []

        list of menu classes: example: ``_menus = [MyAppMenu]``

    .. attribute:: name = None

        name of the apphook (required)

    .. attribute:: app_name = None

        name of the app, this enables Django namespaces support (optional)

    .. attribute:: app_config = None

        configuration model (optional)

    .. attribute:: permissions = True

        if set to true, apphook inherits permissions from the current page

    .. attribute:: exclude_permissions = []

        list of application names to exclude from inheriting CMS permissions


    .. method:: get_configs()

        Returns all the apphook configuration instances.

    .. method:: get_config(namespace)

        Returns the apphook configuration instance linked to the given namespace

    .. method:: get_config_add_url()

        Returns the url to add a new apphook configuration instance
        (usually the model admin add view)

    .. method:: get_menus(page, language, **kwargs)

            Returns the menus for the apphook instance, eventually selected according
            to the given arguments.

            By default it returns the menus assigned to :py:attr:`CMSApp._menus`

            If no page and language si provided, this method **must** return all the
            menus used by this apphook. Example::

                if page and page.reverse_id == 'page1':
                    return [Menu1]
                elif page and page.reverse_id == 'page2':
                    return [Menu2]
                else:
                    return [Menu1, Menu2]

            :param page: page the apphook is attached to
            :param language: current site language
            :return: list of menu classes

    .. method:: get_urls(page, language, **kwargs)

            Returns the urlconfs for the apphook instance, eventually selected
            according to the given arguments.

            By default it returns the urls assigned to :py:attr:`CMSApp._urls`

            This method **must** return a non empty list of urlconfs,
            even if no argument is passed.

            :param page: page the apphook is attached to
            :param language: current site language
            :return: list of urlconfs strings

***************
cms.plugin_base
***************

.. module:: cms.plugin_base

.. class:: CMSPluginBase

    Inherits ``django.contrib.admin.options.ModelAdmin``.

    .. attribute:: admin_preview

        Defaults to ``False``, if ``True``, displays a preview in the admin.

    .. attribute:: cache

        If present and set to ``False``, the plugin will prevent the caching of
        the resulting page.

        .. important:: Setting this to ``False`` will effectively disable the
                       CMS page cache and all upstream caches for pages where
                       the plugin appears. This may be useful in certain cases
                       but for general cache management, consider using the much
                       more capable :meth:`get_cache_expiration`.

    .. attribute:: change_form_template

        Custom template to use to render the form to edit this plugin.

    .. attribute:: form

        Custom form class to be used to edit this plugin.

    .. method:: get_plugin_urls(instance)

        Returns URL patterns for which the plugin wants to register views for.
        They are included under django CMS PageAdmin in the plugin path
        (e.g.: ``/admin/cms/page/plugin/<plugin-name>/`` in the default case).
        Useful if your plugin needs to asynchronously talk to the admin.

    .. attribute:: model

        Is the :class:`CMSPlugin` model we created earlier. If you don't need
        model because you just want to display some template logic, use
        :class:`CMSPlugin` from :mod:`cms.models` as the model instead.

    .. attribute:: module

        Will group the plugin in the plugin editor. If module is ``None``,
        plugin is grouped "Generic" group.

    .. attribute:: name

        Will be displayed in the plugin editor.

    .. attribute:: render_plugin

        If set to ``False``, this plugin will not be rendered at all.

    .. attribute:: render_template

        Will be rendered with the context returned by the render function.

    .. attribute:: text_enabled

        Whether this plugin can be used in text plugins or not.

    .. method:: icon_alt(instance)

        Returns the alt text for the icon used in text plugins, see
        :meth:`icon_src`.

    .. method:: icon_src(instance)

        Returns the URL to the icon to be used for the given instance when that
        instance is used inside a text plugin.

    .. method:: get_cache_expiration(request, instance, placeholder)

        Provides expiration value to the placeholder, and in turn to the page
        for determining the appropriate Cache-Control headers to add to the
        HTTPResponse object.

        Must return one of:

            :``None``:
                This means the placeholder and the page will not even consider
                this plugin when calculating the page expiration.

            :``datetime``:
                A specific date and time (timezone-aware) in the future when
                this plugin's content expires.

                .. important:: The returned ``datetime`` must be timezone-aware
                               or the plugin will be ignored (with a warning)
                               during expiration calculations.

            :``int``:
                An number of seconds that this plugin's content can be cached.

        There are constants are defined in ``cms.constants`` that may be
        useful: :data:`EXPIRE_NOW` and :data:`MAX_EXPIRATION_TTL`.

        An integer value of ``0`` (zero) or :data:`EXPIRE_NOW` effectively means
        "do not cache". Negative values will be treated as :data:`EXPIRE_NOW`.
        Values exceeding the value :data:`MAX_EXPIRATION_TTL` will be set to
        that value.

        Negative ``timedelta`` values or those greater than :data:`MAX_EXPIRATION_TTL`
        will also be ranged in the same manner.

        Similarly, ``datetime`` values earlier than now will be treated as
        :data:`EXPIRE_NOW`. Values greater than :data:`MAX_EXPIRATION_TTL` seconds in the
        future will be treated as :data:`MAX_EXPIRATION_TTL` seconds in the future.

        :param request: Relevant ``HTTPRequest`` instance.
        :param instance: The ``CMSPlugin`` instance that is being rendered.
        :rtype: ``None`` or ``datetime`` or ``int``


    .. method:: get_vary_cache_on(request, instance, placeholder):

        Provides ``VARY`` header strings to be considered by the placeholder
        and in turn by the page.

        Must return one of:

            :``None``:
                This means that this plugin declares no headers for the cache
                to be varied upon. (default)

            :string:
                The name of a header to vary caching upon.

            :list of strings:
                A list of strings, each corresponding to a header to vary the
                cache upon.


    .. method:: render(context, instance, placeholder)

        This method returns the context to be used to render the template
        specified in :attr:`render_template`.

        It's recommended to always populate the context with default values
        by calling the render method of the super class::

            def render(self, context, instance, placeholder):
                context = super(MyPlugin, self).render(context, instance, placeholder)
                ...
                return context


        :param context: Current template context.
        :param instance: Plugin instance that is being rendered.
        :param placeholder: Name of the placeholder the plugin is in.
        :rtype: ``dict``


.. class:: PluginMenuItem

    .. method:: __init___(name, url, data, question=None, action='ajax', attributes=None)

        Creates an item in the plugin / placeholder menu

        :param name: Item name (label)
        :param url: URL the item points to. This URL will be called using POST
        :param data: Data to be POSTed to the above URL
        :param question: Confirmation text to be shown to the user prior to call the given URL (optional)
        :param action: Custom action to be called on click; currently supported: 'ajax', 'ajax_add'
        :param attributes: Dictionary whose content will be addes as data-attributes to the menu item

.. _toolbar-api-reference:

***********
cms.toolbar
***********


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

.. module:: cms.toolbar.toolbar


.. class:: CMSToolbar

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

    .. method:: get_or_create_menu(key. verbose_name, side=LEFT, position=NOne)

        If a menu with ``key`` already exists, this method will return that
        menu. Otherwise it will create a menu for that ``key`` with the given
        ``verbose_name`` on ``side`` at ``position`` and return it.

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


**********
menus.base
**********

.. module:: menus.base

.. class:: NavigationNode(title, url, id[, parent_id=None][, parent_namespace=None][, attr=None][, visible=True])

    A navigation node in a menu tree.

    :param string title: The title to display this menu item with.
    :param string url: The URL associated with this menu item.
    :param id: Unique (for the current tree) ID of this item.
    :param parent_id: Optional, ID of the parent item.
    :param parent_namespace: Optional, namespace of the parent.
    :param dict attr: Optional, dictionary of additional information to store on
                      this node.
    :param bool visible: Optional, defaults to ``True``, whether this item is
                         visible or not.


    .. attribute:: attr

        A dictionary of various additional information describing the node.
        Nodes that represent CMS pages have the following keys in attr:

        * **auth_required** (*bool*) – is authentication required to access this page
        * **is_page** (*bool*) – Always True
        * **navigation_extenders** (*list*) – navigation extenders connected to this node (including Apphooks)
        * **redirect_url** (*str*) – redirect URL of page (if any)
        * **reverse_id** (*str*) – unique identifier for the page
        * **soft_root** (*bool*) – whether page is a soft root
        * **visible_for_authenticated** (*bool*) – visible for authenticated users
        * **visible_for_anonymous** (*bool*) – visible for anonymous users

    .. method:: get_descendants

        Returns a list of all children beneath the current menu item.

    .. method:: get_ancestors

        Returns a list of all parent items, excluding the current menu item.

    .. method:: get_absolute_url

        Utility method to return the URL associated with this menu item,
        primarily to follow naming convention asserted by Django.

    .. method:: get_menu_title

        Utility method to return the associated title, using the same naming
        convention used by :class:`cms.models.pagemodel.Page`.


