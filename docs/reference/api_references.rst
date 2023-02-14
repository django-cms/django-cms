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

    Used for the ``limit_visibility_in_menu`` keyword argument to
    :func:`create_page`. Does not limit menu visibility.


.. data:: VISIBILITY_USERS

    Used for the ``limit_visibility_in_menu`` keyword argument to
    :func:`create_page`. Limits menu visibility to authenticated users.

.. data:: VISIBILITY_ANONYMOUS

    Used for the ``limit_visibility_in_menu`` keyword argument to
    :func:`create_page`. Limits menu visibility to anonymous (not authenticated) users.


.. function:: create_page(title, template, language, menu_title=None, slug=None, apphook=None, apphook_namespace=None, redirect=None, meta_description=None, created_by='python-api', parent=None, publication_date=None, publication_end_date=None, in_navigation=False, soft_root=False, reverse_id=None, navigation_extenders=None, published=False, site=None, login_required=False, limit_visibility_in_menu=VISIBILITY_ALL, position="last-child", overwrite_url=None, xframe_options=Page.X_FRAME_OPTIONS_INHERIT)

    Creates a :class:`cms.models.Page` instance and returns it. Also
    creates a :class:`cms.models.Title` instance for the specified
    language.

    :param str title: Title of the page
    :param str template: Template to use for this page. Must be in :setting:`CMS_TEMPLATES`
    :param str language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param str menu_title: Menu title for this page
    :param str slug: Slug for the page, by default uses a slugified version of *title*
    :param apphook: Application to hook on this page, must be a valid apphook
    :type apphook: str or :class:`cms.app_base.CMSApp` sub-class
    :param str apphook_namespace: Name of the apphook namespace
    :param str redirect: URL redirect
    :param str meta_description: Description of this page for SEO
    :param created_by: User that is creating this page
    :type created_by: str of :class:`django.contrib.auth.models.User` instance
    :param parent: Parent page of this page
    :type parent: :class:`cms.models.Page` instance
    :param datetime.datetime publication_date: Date to publish this page
    :param datetime.datetime publication_end_date: Date to unpublish this page
    :param bool in_navigation: Whether this page should be in the navigation or not
    :param bool soft_root: Whether this page is a soft root or not
    :param str reverse_id: Reverse ID of this page (for template tags)
    :param str navigation_extenders: Menu to attach to this page. Must be a valid menu
    :param bool published: Whether this page should be published or not
    :param site: Site to put this page on
    :type site: :class:`django.contrib.sites.models.Site` instance
    :param bool login_required: Whether users must be logged in or not to view this page
    :param limit_visibility_in_menu: Limits visibility of this page in the menu
    :type limit_visibility_in_menu: :data:`VISIBILITY_ALL` or :data:`VISIBILITY_USERS` or :data:`VISIBILITY_ANONYMOUS`
    :param str position: Where to insert this node if *parent* is given, must be ``'first-child'`` or ``'last-child'``
    :param str   overwrite_url: Overwritten path for this page
    :param int xframe_options: X Frame Option value for Clickjacking protection
    :param str page_title: Overridden page title for HTML title tag


.. function:: create_title(language, title, page, menu_title=None, slug=None, redirect=None, meta_description=None, parent=None, overwrite_url=None)

    Creates a :class:`cms.models.Title` instance and returns it.

    :param str language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param str title: Title of the page
    :param page: The page for which to create this title
    :type page: :class:`cms.models.Page` instance
    :param str menu_title: Menu title for this page
    :param str slug: Slug for the page, by default uses a slugified version of *title*
    :param str redirect: URL redirect
    :param str meta_description: Description of this page for SEO
    :param parent: Used for automated slug generation
    :type parent: :class:`cms.models.Page` instance
    :param str overwrite_url: Overwritten path for this page
    :param str page_title: Overridden page title for HTML title tag


.. function:: add_plugin(placeholder, plugin_type, language, position='last-child', target=None,  **data)

    Adds a plugin to a placeholder and returns it.

    :param placeholder: Placeholder to add the plugin to
    :type placeholder: :class:`cms.models.placeholdermodel.Placeholder` instance
    :param plugin_type: What type of plugin to add
    :type plugin_type: str or :class:`cms.plugin_base.CMSPluginBase` sub-class, must be a valid plugin
    :param str language: Language code for this plugin, must be in :setting:`django:LANGUAGES`
    :param str position: Position to add this plugin to the placeholder, must be a valid django-treebeard ``pos``
        value for :meth:`treebeard:treebeard.models.Node.add_sibling`
    :param target: Parent plugin. Must be plugin instance
    :param data: Data for the plugin type instance


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
    :class:`cms.models.PagePermission` object that gets
    created.

    :param page: The page to assign the user to
    :type page: :class:`cms.models.Page` instance
    :param user: The user to assign to the page
    :type user: :class:`django.contrib.auth.models.User` instance
    :param grant_on: Controls which pages are affected
    :type grant_on: :data:`cms.models.ACCESS_PAGE`, :data:`cms.models.ACCESS_CHILDREN`, :data:`cms.models.ACCESS_DESCENDANTS` or :data:`cms.models.ACCESS_PAGE_AND_DESCENDANTS`
    :param can_*: Permissions to grant
    :param bool grant_all: Grant all permissions to the user


.. function:: publish_page(page, user, language)

    Publishes a page.

    :param page: The page to publish
    :type page: :class:`cms.models.Page` instance
    :param user: The user that performs this action
    :type user: :class:`django.contrib.auth.models.User` instance
    :param str language: The target language to publish to

.. function:: publish_pages(include_unpublished=False, language=None, site=None)

    Publishes multiple pages defined by parameters.

    :param bool include_unpublished: Set to ``True`` to publish all drafts, including unpublished ones; otherwise, only already published pages will be republished
    :param str language: If given, only pages in this language will be published; otherwise, all languages will be published
    :param site: Specify a site to publish pages for specified site only; if not specified pages from all sites are published
    :type site: :class:`django.contrib.sites.models.Site` instance

    .. note::

        This function is a generator, so you'll need to iterate over the result to actually publish
        all pages. This can be done in a single line using ``list()``:

        .. code-block:: python

            list(publish_pages())

.. function:: get_page_draft(page):

    Returns the draft version of a page, regardless if the passed in
    page is a published version or a draft version.

    :param page: The page to get the draft version
    :type page: :class:`cms.models.Page` instance
    :return page: draft version of the page

.. function:: copy_plugins_to_language(page, source_language, target_language, only_empty=True):

    Copy the plugins to another language in the same page for all the page
    placeholders.

    By default plugins are copied only if placeholder has no plugin for the target language; use ``only_empty=False`` to change this.

    .. warning:: This function skips permissions checks

    :param page: the page to copy
    :type page: :class:`cms.models.Page` instance
    :param str source_language: The source language code, must be in :setting:`django:LANGUAGES`
    :param str target_language: The source language code, must be in :setting:`django:LANGUAGES`
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

..  module:: cms.constants

..  data:: TEMPLATE_INHERITANCE_MAGIC

    The token used to identify when a user selects "inherit" as template for a
    page.

..  data:: LEFT

    Used as a position indicator in the toolbar.

..  data:: RIGHT

    Used as a position indicator in the toolbar.

..  data:: REFRESH

    Constant used by the toolbar.

..  data:: EXPIRE_NOW

    Constant of 0 (zero) used for cache control headers

..  data:: MAX_EXPIRATION_TTL

    Constant of 31536000 or 365 days in seconds used for cache control headers


************
cms.app_base
************

..  module:: cms.app_base

..  class:: CMSApp

    .. attribute:: _urls

        list of urlconfs: example: ``_urls = ["myapp.urls"]``

    .. attribute:: _menus

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

        ``CMSApp.get_menus`` accepts page, language and generic keyword arguments:
        you can customize this function to return different list of menu classes
        according to the given arguments.

        Returns the menus for the apphook instance, selected according
        to the given arguments.

        By default it returns the menus assigned to :attr:`_menus`

        If no page and language are provided, this method **must** return all the
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

        Returns the URL configurations for the apphook instance, selected
        according to the given arguments.

        By default it returns the urls assigned to :attr:`_urls`

        This method **must** return a non empty list of URL configurations,
        even if no arguments are passed.

        :param page: page the apphook is attached to
        :param language: current site language
        :return: list of strings representing URL configurations
