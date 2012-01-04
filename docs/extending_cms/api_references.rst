##############
API References
##############

*******
cms.api
*******

Python APIs for creating CMS contents. This is done in :mod:`cms.api` and not
on the models and managers, because the direct API via models and managers is
slightly counterintuitive for developers. Also the functions defined in this
module do sanity checks on arguments.
    
.. warning:: None of the functions in this modules do any security or permission
             checks. They verify their input values to be sane wherever
             possible, however permission checks should be implemented manually
             before calling any of these functions.


Functions and constants
=======================

.. module:: cms.api

.. data:: VISIBILITY_ALL

    Used for the ``limit_menu_visibility`` keyword argument to
    :func:`create_page`. Does not limit menu visibility.


.. data:: VISIBILITY_USERS

    Used for the ``limit_menu_visibility`` keyword argument to
    :func:`create_page`. Limits menu visibility to authenticated users.


.. data:: VISIBILITY_STAFF

    Used for the ``limit_menu_visibility`` keyword argument to
    :func:`create_page`. Limits menu visibility to staff users.


.. function:: create_page(title, template, language, menu_title=None, slug=None, apphook=None, redirect=None, meta_description=None, meta_keywords=None, created_by='python-api', parent=None, publication_date=None, publication_end_date=None, in_navigation=False, soft_root=False, reverse_id=None, navigation_extenders=None, published=False, site=None, login_required=False, limit_visibility_in_menu=VISIBILITY_ALL, position="last-child")

    Creates a :class:`cms.models.pagemodel.Page` instance and returns it. Also
    creates a :class:`cms.models.titlemodel.Title` instance for the specified
    language.
    
    :param string title: Title of the page
    :param string template: Template to use for this page. Must be in :setting:`CMS_TEMPLATES`
    :param string language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param string menu_title: Menu title for this page
    :param string slug: Slug for the page, by default uses a slugified version of *title*
    :param apphook: Application to hook on this page, must be a valid apphook
    :type apphook: string or :class:`cms.app_base.CMSApp` subclass
    :param string redirect: URL redirect (only applicable if :setting:`CMS_REDIRECTS` is ``True``)
    :param string meta_description: Description of this page for SEO
    :param string meta_keywords: Keywords for this page for SEO
    :param created_by: User that creates this page
    :type created_by: string of :class:`django.contrib.auth.models.User` instance
    :param parent: Parent page of this page
    :type parent: :class:`cms.models.pagemodel.Page` instance
    :param datetime publication_date: Date to publish this page
    :param datetime publication_end_date: Date to unpublish this page
    :param boolean in_navigation: Whether this page should be in the navigation or not
    :param boolean soft_root: Whether this page is a softroot or not
    :param string reverse_id: Reverse ID of this page (for template tags)
    :param string navigation_extenders: Menu to attach to this page, must be a valid menu
    :param boolean published: Whether this page should be published or not
    :param site: Site to put this page on
    :type site: :class:`django.contrib.sites.models.Site` instance
    :param boolean login_required: Whether users must be logged in or not to view this page
    :param limit_menu_visibility: Limits visibility of this page in the menu
    :type limit_menu_visibility: :data:`VISIBILITY_ALL` or :data:`VISIBILITY_USERS` or :data:`VISIBILITY_STAFF`
    :param string position: Where to insert this node if *parent* is given, must be ``'first-child'`` or ``'last-child'``
    :param string overwrite_url: Overwritten path for this page


.. function:: create_title(language, title, page, menu_title=None, slug=None, apphook=None, redirect=None, meta_description=None, meta_keywords=None, parent=None)
    
    Creates a :class:`cms.models.titlemodel.Title` instance and returns it.

    :param string language: Language code for this page. Must be in :setting:`django:LANGUAGES`
    :param string title: Title of the page
    :param page: The page for which to create this title
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param string menu_title: Menu title for this page
    :param string slug: Slug for the page, by default uses a slugified version of *title*
    :param apphook: Application to hook on this page, must be a valid apphook
    :type apphook: string or :class:`cms.app_base.CMSApp` subclass
    :param string redirect: URL redirect (only applicable if :setting:`CMS_REDIRECTS` is ``True``)
    :param string meta_description: Description of this page for SEO
    :param string meta_keywords: Keywords for this page for SEO
    :param parent: Used for automated slug generation
    :type parent: :class:`cms.models.pagemodel.Page` instance
    :param string overwrite_url: Overwritten path for this page


.. function:: add_plugin(placeholder, plugin_type, language, position='last-child', **data)

    Adds a plugin to a placeholder and returns it.

    :param placeholder: Placeholder to add the plugin to
    :type placeholder: :class:`cms.models.placeholdermodel.Placeholder` instance
    :param plugin_type: What type of plugin to add
    :type plugin_type: string or :class:`cms.plugin_base.CMSPluginBase` subclass, must be a valid plugin
    :param string language: Language code for this plugin, must be in :setting:`django:LANGUAGES`
    :param string position: Position to add this plugin to the placeholder, must be a valid django-mptt position
    :param kwargs data: Data for the plugin type instance


.. function:: create_page_user(created_by, user, can_add_page=True, can_change_page=True, can_delete_page=True, can_recover_page=True, can_add_pageuser=True, can_change_pageuser=True, can_delete_pageuser=True, can_add_pagepermission=True, can_change_pagepermission=True, can_delete_pagepermission=True, grant_all=False) 
    
    Creates a page user for the user provided and returns that page user.
    
    :param created_by: The user that creates the page user
    :type created_by: :class:`django.contrib.auth.models.User` instance
    :param user: The user to create the page user from
    :type user: :class:`django.contrib.auth.models.User` instance
    :param boolean can_*: Permissions to give the user
    :param boolean grant_all: Grant all permissions to the user


.. function:: assign_user_to_page(page, user, grant_on=ACCESS_PAGE_AND_DESCENDANTS, can_add=False, can_change=False, can_delete=False, can_change_advanced_settings=False, can_publish=False, can_change_permissions=False, can_move_page=False, can_moderate=False, grant_all=False)
    
    Assigns a user to a page and gives them some permissions. Returns the 
    :class:`cms.models.permissionmodels.PagePermission` object that gets
    created.
    
    :param page: The page to assign the user to
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param user: The user to assign to the page
    :type user: :class:`django.contrib.auth.models.User` instance
    :param grant_on: Controls which pages are affected
    :type grant_on: :data:`cms.models.moderatormodels.ACCESS_PAGE`, :data:`cms.models.moderatormodels.ACCESS_CHILDREN`, :data:`cms.models.moderatormodels.ACCESS_DESCENDANTS` or :data:`cms.models.moderatormodels.ACCESS_PAGE_AND_DESCENDANTS`
    :param can_*: Permissions to grant
    :param boolean grant_all: Grant all permissions to the user
    

.. function:: publish_page(page, user, approve=False)

    Publishes a page and optionally approves that publication.
    
    :param page: The page to publish
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param user: The user that performs this action
    :type user: :class:`django.contrib.auth.models.User` instance
    :param boolean approve: Whether to approve the publication or not
    

.. function:: approve_page(page, user)

    Approves a page.
    
    :param page: The page to approve
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param user: The user that performs this action
    :type user: :class:`django.contrib.auth.models.User` instance


Example workflows
=================

Create a page called ``'My Page`` using the template ``'my_template.html'`` and
add a text plugin with the content ``'hello world'``. This is done in English::

    from cms.api import create_page, add_plugin
    
    page = create_page('My Page', 'my_template.html', 'en')
    placeholder = page.placeholders.get(slot='body')
    add_plugin(placeholder, 'TextPlugin', 'en', body='hello world')


***************
cms.plugin_base
***************

.. module:: cms.plugin_base

.. class:: CMSPluginBase

    Inherits ``django.contrib.admin.options.ModelAdmin``.
        
    .. attribute:: admin_preview
    
        Defaults to ``True``, if ``False`` no preview is done in the admin.
        
    .. attribute:: change_form_template

        Custom template to use to render the form to edit this plugin.    
    
    .. attribute:: form
    
        Custom form class to be used to edit this plugin.

    .. attribute:: model

        Is the :class:`CMSPlugin` model we created earlier. If you don't need
        model because you just want to display some template logic, use
        :class:`CMSPlugin` from :mod:`cms.models` as the model instead.
        
    .. attribute:: module

        Will be group the plugin in the plugin editor. If module is ``None``,
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
    
        Returns the url to the icon to be used for the given instance when that
        instance is used inside a text plugin.
        
    .. method:: render(context, instance, placeholder)
    
        This method returns the context to be used to render the template
        specified in :attr:`render_template`.
        
        :param context: Current template context.
        :param instance: Plugin instance that is being rendered.
        :param placeholder: Name of the placeholder the plugin is in.
        :rtype: ``dict``


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

