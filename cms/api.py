"""
Python APIs for creating CMS content. This is done in :mod:`cms.api` and not
on the models and managers, because the direct API via models and managers is
slightly counterintuitive for developers.

The api for both Pages and Plugins has changed significantly since django CMS
Version 4.

Also, the functions defined in this module do sanity checks on arguments.

.. warning:: None of the functions in this module does any security or permission
             checks. They verify their input values to be sane wherever
             possible, however permission checks should be implemented manually
             before calling any of these functions.

.. info:: Due to potential circular dependency issues, it's recommended
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

"""
import warnings

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import FieldError, ValidationError
from django.db import transaction
from django.template.defaultfilters import slugify
from django.template.loader import get_template

from cms import constants
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import PageContent
from cms.models.pagemodel import Page
from cms.models.permissionmodels import (
    ACCESS_PAGE_AND_DESCENDANTS,
    GlobalPagePermission,
    PagePermission,
    PageUser,
)
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils import get_current_site
from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_list
from cms.utils.page import get_available_slug, get_clean_username
from cms.utils.permissions import _thread_locals
from cms.utils.plugins import copy_plugins_to_placeholder
from menus.menu_pool import menu_pool

# ===============================================================================
# Helpers/Internals
# ===============================================================================


def _verify_apphook(apphook, namespace):
    """
    Verifies the apphook given is valid and returns the normalized form (name)
    """
    apphook_pool.discover_apps()
    if isinstance(apphook, CMSApp):
        try:
            assert apphook.__class__ in [app.__class__ for app in apphook_pool.apps.values()]
        except AssertionError:
            raise
        apphook_name = apphook.__class__.__name__
    elif hasattr(apphook, '__module__') and issubclass(apphook, CMSApp):
        return apphook.__name__
    elif isinstance(apphook, str):
        try:
            assert apphook in apphook_pool.apps
        except AssertionError:
            raise
        apphook_name = apphook
    else:
        raise TypeError("apphook must be string or CMSApp instance")
    if apphook_pool.apps[apphook_name].app_name and not namespace:
        raise ValidationError('apphook with app_name must define a namespace')
    return apphook_name


def _verify_plugin_type(plugin_type):
    """
    Verifies the given plugin_type is valid and returns a tuple of
    (plugin_model, plugin_type)
    """
    if hasattr(plugin_type, '__module__') and issubclass(plugin_type, CMSPluginBase):
        plugin_model = plugin_type.model
        assert plugin_type in plugin_pool.plugins.values()
        plugin_type = plugin_type.__name__
    elif isinstance(plugin_type, str):
        try:
            plugin_model = plugin_pool.get_plugin(plugin_type).model
        except KeyError:
            raise TypeError(
                'plugin_type must be CMSPluginBase subclass or string'
            )
    else:
        raise TypeError('plugin_type must be CMSPluginBase subclass or string')
    return plugin_model, plugin_type


# ===============================================================================
# Public API
# ===============================================================================

@transaction.atomic
def create_page(title, template, language, menu_title=None, slug=None,
                apphook=None, apphook_namespace=None, redirect=None, meta_description=None,
                created_by='python-api', parent=None,
                publication_date=None, publication_end_date=None,
                in_navigation=False, soft_root=False, reverse_id=None,
                navigation_extenders=None, published=None, site=None,
                login_required=False, limit_visibility_in_menu=constants.VISIBILITY_ALL,
                position="last-child", overwrite_url=None,
                xframe_options=constants.X_FRAME_OPTIONS_INHERIT):
    """
    Creates a :class:`cms.models.Page` instance and returns it. Also
    creates a :class:`cms.models.PageContent` instance for the specified
    language.

    .. warning::
        Since version 4 the parameters published, publication_date, and publication_end_date
        do not change the behaviour of this function. If they are supplied a warning is raised.

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
    :param bool in_navigation: Whether this page should be in the navigation or not
    :param bool soft_root: Whether this page is a soft root or not
    :param str reverse_id: Reverse ID of this page (for template tags)
    :param str navigation_extenders: Menu to attach to this page. Must be a valid menu
    :param site: Site to put this page on
    :type site: :class:`django.contrib.sites.models.Site` instance
    :param bool login_required: Whether users must be logged in or not to view this page
    :param limit_visibility_in_menu: Limits visibility of this page in the menu
    :type limit_visibility_in_menu: :data:`VISIBILITY_ALL` or :data:`VISIBILITY_USERS` or :data:`VISIBILITY_ANONYMOUS`
    :param str position: Where to insert this node if *parent* is given, must be ``'first-child'`` or ``'last-child'``
    :param str   overwrite_url: Overwritten path for this page
    :param int xframe_options: X Frame Option value for Clickjacking protection
    :param str page_title: Overridden page title for HTML title tag
    """
    if published is not None or publication_date is not None or publication_end_date is not None:
        warnings.warn('This API function no longer accepts a "published", "publication_date", or '
                      '"publication_end_date" argument', UserWarning, stacklevel=2)

    # validate template
    if not template == TEMPLATE_INHERITANCE_MAGIC:
        assert template in [tpl[0] for tpl in get_cms_setting('TEMPLATES')]
        get_template(template)

    # validate site
    if not site:
        site = get_current_site()
    else:
        assert isinstance(site, Site)

    # validate language:
    assert language in get_language_list(site), get_cms_setting('LANGUAGES').get(site.pk)

    # validate parent
    if parent:
        assert isinstance(parent, Page)

    if navigation_extenders:
        raw_menus = menu_pool.get_menus_by_attribute("cms_enabled", True)
        menus = [menu[0] for menu in raw_menus]
        assert navigation_extenders in menus

    # validate menu visibility
    accepted_limitations = (constants.VISIBILITY_ALL, constants.VISIBILITY_USERS, constants.VISIBILITY_ANONYMOUS)
    assert limit_visibility_in_menu in accepted_limitations

    # validate position
    assert position in ('last-child', 'first-child', 'left', 'right')
    target_node = parent.node if parent else None

    # validate and normalize apphook
    if apphook:
        application_urls = _verify_apphook(apphook, apphook_namespace)
    else:
        application_urls = None

    # ugly permissions hack
    if created_by and isinstance(created_by, get_user_model()):
        _thread_locals.user = created_by
        created_by = get_clean_username(created_by)
    else:
        _thread_locals.user = None

    if reverse_id:
        if Page.objects.filter(reverse_id=reverse_id, node__site=site).exists():
            raise FieldError('A page with the reverse_id="%s" already exist.' % reverse_id)

    page = Page(
        created_by=created_by,
        changed_by=created_by,
        reverse_id=reverse_id,
        navigation_extenders=navigation_extenders,
        application_urls=application_urls,
        application_namespace=apphook_namespace,
        login_required=login_required,
    )
    page.set_tree_node(site=site, target=target_node, position=position)
    page.save()

    create_page_content(
        language=language,
        title=title,
        menu_title=menu_title,
        slug=slug,
        created_by=created_by,
        redirect=redirect,
        meta_description=meta_description,
        page=page,
        overwrite_url=overwrite_url,
        soft_root=soft_root,
        in_navigation=in_navigation,
        template=template,
        limit_visibility_in_menu=limit_visibility_in_menu,
        xframe_options=xframe_options,
    )

    if parent and position in ('last-child', 'first-child'):
        parent._clear_node_cache()

    del _thread_locals.user
    return page


@transaction.atomic
def create_page_content(language, title, page, menu_title=None, slug=None,
                        redirect=None, meta_description=None, parent=None,
                        overwrite_url=None, page_title=None, path=None,
                        created_by='python-api', soft_root=False, in_navigation=False,
                        template=TEMPLATE_INHERITANCE_MAGIC,
                        limit_visibility_in_menu=constants.VISIBILITY_ALL,
                        xframe_options=constants.X_FRAME_OPTIONS_INHERIT):
    """
    Creates a :class:`cms.models.PageContent` instance and returns it.

    ``parent`` is only used if slug=None.

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

    """
    # validate template
    if not template == TEMPLATE_INHERITANCE_MAGIC:
        assert template in [tpl[0] for tpl in get_cms_setting('TEMPLATES')]
        get_template(template)

    # validate page
    assert isinstance(page, Page)

    # validate language:
    assert language in get_language_list(page.node.site_id)

    # validate menu visibility
    accepted_limitations = (constants.VISIBILITY_ALL, constants.VISIBILITY_USERS, constants.VISIBILITY_ANONYMOUS)
    assert limit_visibility_in_menu in accepted_limitations

    # set default slug:
    if not slug:
        base = page.get_path_for_slug(slugify(title), language)
        slug = get_available_slug(page.node.site, base, language)

    if overwrite_url:
        path = overwrite_url.strip('/')
    elif path is None:
        path = page.get_path_for_slug(slug, language)

    if created_by and isinstance(created_by, get_user_model()):
        _thread_locals.user = created_by
        created_by = get_clean_username(created_by)

    page.urls.create(
        slug=slug,
        path=path,
        page=page,
        managed=not bool(overwrite_url),
        language=language,
    )

    # E.g., djangocms-versioning needs an User object to be passed when creating a versioned Object
    user = getattr(_thread_locals, "user", "unknown user")
    page_content = PageContent.objects.with_user(user).create(
        language=language,
        title=title,
        menu_title=menu_title,
        page_title=page_title,
        redirect=redirect,
        meta_description=meta_description,
        page=page,
        created_by=created_by,
        changed_by=created_by,
        soft_root=soft_root,
        in_navigation=in_navigation,
        template=template,
        limit_visibility_in_menu=limit_visibility_in_menu,
        xframe_options=xframe_options,
    )
    page_content.rescan_placeholders()

    page_languages = page.get_languages()

    if language not in page_languages:
        page.update_languages(page_languages + [language])
    return page_content


def create_title(language, title, page, menu_title=None, slug=None,
                 redirect=None, meta_description=None, parent=None,
                 overwrite_url=None, page_title=None, path=None,
                 created_by='python-api', soft_root=False, in_navigation=False,
                 template=TEMPLATE_INHERITANCE_MAGIC,
                 limit_visibility_in_menu=constants.VISIBILITY_ALL,
                 xframe_options=constants.X_FRAME_OPTIONS_INHERIT):
    """
    .. warning ::
        ``create_title`` has been renamed to ``create_page_content`` as of django CMS version 4.
    """
    warnings.warn(
        "cms.api.create_title has been renamed to cms.api.create_page_content().",
        RemovedInDjangoCMS43Warning,
        stacklevel=2
    )
    return create_page_content(
        language, title, page,
        menu_title=menu_title, slug=slug, redirect=redirect, meta_description=meta_description,
        parent=parent, overwrite_url=overwrite_url, page_title=page_title, path=path,
        created_by=created_by, soft_root=soft_root, in_navigation=in_navigation, template=template,
        limit_visibility_in_menu=limit_visibility_in_menu, xframe_options=xframe_options
    )


@transaction.atomic
def add_plugin(placeholder, plugin_type, language, position='last-child',
               target=None, **data):
    """
    Adds a plugin to a placeholder and returns it.

    :param placeholder: Placeholder to add the plugin to
    :type placeholder: :class:`cms.models.placeholdermodel.Placeholder` instance
    :param plugin_type: What type of plugin to add
    :type plugin_type: str or :class:`cms.plugin_base.CMSPluginBase` sub-class, must be a valid plugin
    :param str language: Language code for this plugin, must be in :setting:`django:LANGUAGES`
    :param str position: Position to add this plugin to the placeholder. Allowed positions are ``"last-child"``
                         (default), ``"first-child"``, ``"left"``, ``"right"``.
    :param target: Parent plugin. Must be plugin instance
    :param data: Data for the plugin type instance
    """
    # validate placeholder
    assert isinstance(placeholder, Placeholder)

    # validate and normalize plugin type
    plugin_model, plugin_type = _verify_plugin_type(plugin_type)

    if target:
        if position == 'last-child':
            new_pos = placeholder.get_next_plugin_position(language, parent=target, insert_order='last')
            parent_id = target.pk
        elif position == 'first-child':
            new_pos = placeholder.get_next_plugin_position(language, parent=target, insert_order='first')
            parent_id = target.pk
        elif position == 'left':
            new_pos = target.position
            parent_id = target.parent_id
        elif position == 'right':
            new_pos = target.position + 1 + target._get_descendants_count()
            parent_id = target.parent_id
        else:
            raise Exception('position not supported: %s' % position)
    else:
        assert position in ('first-child', 'last-child')
        if position == 'last-child':
            new_pos = placeholder.get_next_plugin_position(language, insert_order='last')
        else:
            new_pos = 1
        parent_id = None

    plugin_base = CMSPlugin(
        plugin_type=plugin_type,
        placeholder=placeholder,
        position=new_pos,
        language=language,
        parent_id=parent_id,
    )
    plugin_base = placeholder.add_plugin(plugin_base)
    plugin = plugin_model(**data)
    plugin_base.set_base_attr(plugin)
    plugin.save()
    return plugin


def create_page_user(created_by, user,
                     can_add_page=True, can_view_page=True,
                     can_change_page=True, can_delete_page=True,
                     can_publish_page=True, can_add_pageuser=True,
                     can_change_pageuser=True, can_delete_pageuser=True,
                     can_add_pagepermission=True,
                     can_change_pagepermission=True,
                     can_delete_pagepermission=True, grant_all=False):
    """
    Creates a page user for the user provided and returns that page user.

    :param created_by: The user that creates the page user
    :type created_by: :class:`django.contrib.auth.models.User` instance
    :param user: The user to create the page user from
    :type user: :class:`django.contrib.auth.models.User` instance
    :param bool can_*: Permissions to give the user
    :param bool grant_all: Grant all permissions to the user
    """
    from cms.admin.forms import save_permissions
    if grant_all:
        # just be lazy
        return create_page_user(created_by, user, True, True, True, True,
                                True, True, True, True, True, True, True)

    # validate created_by
    assert isinstance(created_by, get_user_model())

    data = {
        'can_add_page': can_add_page,
        'can_view_page': can_view_page,
        'can_change_page': can_change_page,
        'can_delete_page': can_delete_page,
        'can_publish_page': can_publish_page,
        'can_add_pageuser': can_add_pageuser,
        'can_change_pageuser': can_change_pageuser,
        'can_delete_pageuser': can_delete_pageuser,
        'can_add_pagepermission': can_add_pagepermission,
        'can_change_pagepermission': can_change_pagepermission,
        'can_delete_pagepermission': can_delete_pagepermission,
    }
    user.is_staff = True
    user.is_active = True
    page_user = PageUser(created_by=created_by)
    for field in [f.name for f in get_user_model()._meta.local_fields]:
        setattr(page_user, field, getattr(user, field))
    user.save()
    page_user.save()
    save_permissions(data, page_user)
    return user


def assign_user_to_page(page, user, grant_on=ACCESS_PAGE_AND_DESCENDANTS,
                        can_add=False, can_change=False, can_delete=False,
                        can_change_advanced_settings=False, can_publish=None,
                        can_change_permissions=False, can_move_page=False,
                        can_recover_page=True, can_view=False,
                        grant_all=False, global_permission=False):
    """
    Assigns a user to a page and gives them some permissions. Returns the
    :class:`cms.models.PagePermission` object that gets
    created.

    :param page: The page to assign the user to
    :type page: :class:`cms.models.Page` instance
    :param user: The user to assign to the page
    :type user: :class:`django.contrib.auth.models.User` instance
    :param grant_on: Controls which pages are affected
    :type grant_on: :data:`cms.models.ACCESS_PAGE`, :data:`cms.models.ACCESS_CHILDREN`,
    :data:`cms.models.ACCESS_DESCENDANTS` or :data:`cms.models.ACCESS_PAGE_AND_DESCENDANTS`
    :param can_*: Permissions to grant
    :param bool grant_all: Grant all permissions to the user
    """

    grant_all = grant_all and not global_permission
    data = {
        'can_add': can_add or grant_all,
        'can_change': can_change or grant_all,
        'can_delete': can_delete or grant_all,
        'can_publish': can_publish or grant_all,
        'can_change_advanced_settings': can_change_advanced_settings or grant_all,
        'can_change_permissions': can_change_permissions or grant_all,
        'can_move_page': can_move_page or grant_all,
        'can_view': can_view or grant_all,
    }

    page_permission = PagePermission(page=page, user=user,
                                     grant_on=grant_on, **data)
    page_permission.save()
    if global_permission:
        page_permission = GlobalPagePermission(
            user=user, can_recover_page=can_recover_page, **data)
        page_permission.save()
        page_permission.sites.add(get_current_site())
    return page_permission


def publish_page(page, user, language):
    """
    .. warning::

        Publishing pages has been removed from django CMS core in version 4 onward.

        For publishing functionality see `djangocms-versioning: <https://github.com/django-cms/djangocms-versioning>`_
    """
    warnings.warn('This API function has been removed. For publishing functionality use a package that adds '
                  'publishing, such as: djangocms-versioning.',
                  UserWarning, stacklevel=2)


def publish_pages(include_unpublished=False, language=None, site=None):
    """
    .. warning::

        Publishing pages has been removed from django CMS core in version 4 onward.

        For publishing functionality see `djangocms-versioning: <https://github.com/django-cms/djangocms-versioning>`_
    """
    warnings.warn('This API function has been removed. For publishing functionality use a package that adds '
                  'publishing, such as: djangocms-versioning.',
                  UserWarning, stacklevel=2)


def get_page_draft(page):
    """
     .. warning::

        The concept of draft pages has been removed from django CMS core in version 4 onward.

        For draft functionality see `djangocms-versioning: <https://github.com/django-cms/djangocms-versioning>`_
    """
    warnings.warn('This API function has been removed. For publishing functionality use a package that adds '
                  'publishing, such as: djangocms-versioning.',
                  UserWarning, stacklevel=2)


def copy_plugins_to_language(page, source_language, target_language,
                             only_empty=True):
    """
    Copy the plugins to another language in the same page for all the page
    placeholders.

    By default, plugins are copied only if placeholder has no plugin for the
    target language; use ``only_empty=False`` to change this.

    .. warning: This function skips permissions checks

    :param page: the page to copy
    :type page: :class:`cms.models.pagemodel.Page` instance
    :param string source_language: The source language code,
     must be in :setting:`django:LANGUAGES`
    :param string target_language: The source language code,
     must be in :setting:`django:LANGUAGES`
    :param bool only_empty: if False, plugin are copied even if
     plugins exists in the target language (on a placeholder basis).
    :return int: number of copied plugins
    """
    copied = 0
    placeholders = page.get_placeholders(source_language)
    for placeholder in placeholders:
        # only_empty is True we check if the placeholder already has plugins and
        # we skip it if has some
        if not only_empty or not placeholder.get_plugins(language=target_language).exists():
            plugins = list(placeholder.get_plugins(language=source_language))
            copied_plugins = copy_plugins_to_placeholder(plugins, placeholder, language=target_language)
            copied += len(copied_plugins)
    return copied


def can_change_page(request):
    """
    Check whether a user has the permission to change the page.

    This will work across all permission-related setting, with a unified interface
    to permission checking.

    :param request: The request object from which the user will be taken.
    :type request: :class:`HttpRequest` instance

    """
    from cms.utils import page_permissions

    user = request.user
    current_page = request.current_page

    if current_page:
        return page_permissions.user_can_change_page(user, current_page)

    site = Site.objects.get_current(request)
    return page_permissions.user_can_change_all_pages(user, site)
