####
APIs
####

..  module:: cms.api

Python APIs for creating and manipulating django CMS content.

These APIs are provided in order to provide a stable abstraction layer between internal django CMS functions and
external code.

The APIs also make access to the functionality simpler, by providing more intuitive interface, with better
input-checking.

..  warning::

    None of the functions in this module make any security or permissions checks. They verify their input values for
    validity and make some basic sanity checks, but permissions checks should be implemented manually before calling any
    of these functions.

..  warning::

     Due to potential circular dependency issues, we recommend that you import the APIs in the functions that use them.
     Use::

         def my_function():
             from cms.api import api_function

             api_function(...)

     rather than::

         from cms.api import api_function

         def my_function():
             api_function(...)


..  function:: create_page(title, template, language, menu_title=None, slug=None, apphook=None, apphook_namespace=None, redirect=None, meta_description=None, created_by='python-api', parent=None, publication_date=None, publication_end_date=None, in_navigation=False, soft_root=False, reverse_id=None, navigation_extenders=None, published=False, site=None, login_required=False, limit_visibility_in_menu=VISIBILITY_ALL, position="last-child", overwrite_url=None, xframe_options=Page.X_FRAME_OPTIONS_INHERIT, with_revision=False)

    Creates a :class:`cms.models.Page` instance and returns it. Also
    creates a :class:`cms.models.Title` instance for the specified
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
    :type parent: :class:`cms.models.Page` instance
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
    :type limit_menu_visibility: :data:`~cms.constants.VISIBILITY_ALL`, \
         :data:`~cms.constants.VISIBILITY_USERS` or \
         :data:`~cms.constants.VISIBILITY_ANONYMOUS`
    :param string position: Where to insert this node if *parent* is given, must be ``'first-child'`` or \
        ``'last-child'``
    :param string overwrite_url: Overwritten path for this page
    :param int xframe_options: X Frame Option value for Clickjacking protection
    :param bool with_revision: Whether to create a revision for the new page.


..  function:: create_title(language, title, page, menu_title=None, slug=None, redirect=None, meta_description=None, parent=None, overwrite_url=None, with_revision=False)

    Creates a :class:`cms.models.Title` instance and returns it.

    :param string language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param string title: Title of the page
    :param page: The page for which to create this title
    :type page: :class:`cms.models.Page` instance
    :param string menu_title: Menu title for this page
    :param string slug: Slug for the page, by default uses a slugified version of *title*
    :param string redirect: URL redirect
    :param string meta_description: Description of this page for SEO
    :param parent: Used for automated slug generation
    :type parent: :class:`cms.models.Page` instance
    :param string overwrite_url: Overwritten path for this page
    :param bool with_revision: Whether to create a revision for the new page.


..  function:: add_plugin(placeholder, plugin_type, language, position='last-child', target=None,  **data)

    Adds a plugin to a placeholder and returns it.

    :param placeholder: Placeholder to add the plugin to
    :type placeholder: :class:`cms.models.Placeholder` instance
    :param plugin_type: What type of plugin to add
    :type plugin_type: string or :class:`cms.plugin_base.CMSPluginBase` sub-class, must be a valid plugin
    :param string language: Language code for this plugin, must be in :setting:`django:LANGUAGES`
    :param string position: Position to add this plugin to the placeholder, must be a valid django-mptt position
    :param target: Parent plugin. Must be plugin instance
    :param data: Data for the plugin type instance


..  function:: create_page_user(created_by, user, can_add_page=True, can_change_page=True, can_delete_page=True, can_recover_page=True, can_add_pageuser=True, can_change_pageuser=True, can_delete_pageuser=True, can_add_pagepermission=True, can_change_pagepermission=True, can_delete_pagepermission=True, grant_all=False)

    Creates a page user for the user provided and returns that page user.

    :param created_by: The user that creates the page user
    :type created_by: :class:`django.contrib.auth.models.User` instance
    :param user: The user to create the page user from
    :type user: :class:`django.contrib.auth.models.User` instance
    :param bool can_*: Permissions to give the user
    :param bool grant_all: Grant all permissions to the user


..  function:: assign_user_to_page(page, user, grant_on=ACCESS_PAGE_AND_DESCENDANTS, can_add=False, can_change=False, can_delete=False, can_change_advanced_settings=False, can_publish=False, can_change_permissions=False, can_move_page=False, grant_all=False)

    Assigns a user to a page and gives them some permissions. Returns the
    :class:`cms.models.PagePermission` object that gets
    created.

    :param page: The page to assign the user to
    :type page: :class:`cms.models.Page` instance
    :param user: The user to assign to the page
    :type user: :class:`django.contrib.auth.models.User` instance
    :param grant_on: Controls which pages are affected
    :type grant_on: :data:`~cms.models.ACCESS_PAGE`, :data:`~cms.models.ACCESS_CHILDREN`, \
        :data:`~cms.models.ACCESS_DESCENDANTS` or :data:`~cms.models.ACCESS_PAGE_AND_DESCENDANTS`
    :param can_*: Permissions to grant
    :param bool grant_all: Grant all permissions to the user


..  function:: publish_page(page, user, language)

    Publishes a page.

    :param page: The page to publish
    :type page: :class:`cms.models.Page` instance
    :param user: The user that performs this action
    :type user: :class:`django.contrib.auth.models.User` instance
    :param string language: The target language to publish to


..  function:: publish_pages(include_unpublished=False, language=None, site=None)

    Publishes multiple pages defined by parameters.

    :param bool include_unpublished: Set to ``True`` to publish all drafts, including unpublished ones; otherwise, only already published pages will be republished
    :param string language: If given, only pages in this language will be published; otherwise, all languages will be published
    :param site: Specify a site to publish pages for specified site only; if not specified pages from all sites are published
    :type site: :class:`django.contrib.sites.models.Site` instance


..  function:: get_page_draft(page):

    Returns the draft version of a page, regardless if the passed in
    page is a published version or a draft version.

    :param page: The page to get the draft version
    :type page: :class:`cms.models.Page` instance
    :return page: draft version of the page


..  function:: copy_plugins_to_language(page, source_language, target_language, only_empty=True):

    Copy the plugins to another language in the same page for all the page
    placeholders.

    By default plugins are copied only if placeholder has no plugin for the target language; use ``only_empty=False``
    to change this.

    .. warning:: This function skips permissions checks

    :param page: the page to copy
    :type page: :class:`cms.models.Page` instance
    :param string source_language: The source language code, must be in :setting:`django:LANGUAGES`
    :param string target_language: The source language code, must be in :setting:`django:LANGUAGES`
    :param bool only_empty: if False, plugin are copied even if plugins exists in the
     target language (on a placeholder basis).
    :return int: number of copied plugins


Examples of usage can be found in:

* :ref:`write_test`
* :ref:`testing_plugins`
