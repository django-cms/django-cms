# -*- coding: utf-8 -*-
"""
Public Python API to create CMS contents.

WARNING: None of the functions defined in this module checks for permissions.
You must implement the necessary permission checks in your own code before
calling these methods!
"""
import warnings

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import FieldError
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.utils import six

from cms import constants
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models.pagemodel import Page
from cms.models.permissionmodels import (PageUser, PagePermission, GlobalPagePermission,
                                         ACCESS_PAGE_AND_DESCENDANTS)
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils import get_current_site
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_list
from cms.utils.page import get_available_slug, get_clean_username
from cms.utils.permissions import _thread_locals
from cms.utils.plugins import copy_plugins_to_placeholder
from menus.menu_pool import menu_pool


#===============================================================================
# Helpers/Internals
#===============================================================================


def _verify_apphook(apphook, namespace):
    """
    Verifies the apphook given is valid and returns the normalized form (name)
    """
    apphook_pool.discover_apps()
    if isinstance(apphook, CMSApp):
        try:
            assert apphook.__class__ in [app.__class__ for app in apphook_pool.apps.values()]
        except AssertionError:
            print(apphook_pool.apps.values())
            raise
        apphook_name = apphook.__class__.__name__
    elif hasattr(apphook, '__module__') and issubclass(apphook, CMSApp):
        return apphook.__name__
    elif isinstance(apphook, six.string_types):
        try:
            assert apphook in apphook_pool.apps
        except AssertionError:
            print(apphook_pool.apps.values())
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
    if (hasattr(plugin_type, '__module__') and
            issubclass(plugin_type, CMSPluginBase)):
        plugin_model = plugin_type.model
        assert plugin_type in plugin_pool.plugins.values()
        plugin_type = plugin_type.__name__
    elif isinstance(plugin_type, six.string_types):
        try:
            plugin_model = plugin_pool.get_plugin(plugin_type).model
        except KeyError:
            raise TypeError(
                'plugin_type must be CMSPluginBase subclass or string'
            )
    else:
        raise TypeError('plugin_type must be CMSPluginBase subclass or string')
    return plugin_model, plugin_type


#===============================================================================
# Public API
#===============================================================================

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
    Create a CMS Page and it's title for the given language

    See docs/extending_cms/api_reference.rst for more info
    """
    if published != None:
        raise Exception("WTF")
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

    create_title(
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
def create_title(language, title, page, menu_title=None, slug=None,
                 redirect=None, meta_description=None, parent=None,
                 overwrite_url=None, page_title=None, path=None,
                 created_by='python-api', soft_root=False, in_navigation=False,
                 template=TEMPLATE_INHERITANCE_MAGIC,
                 limit_visibility_in_menu=constants.VISIBILITY_ALL,
                 xframe_options=constants.X_FRAME_OPTIONS_INHERIT):
    """
    Create a title.

    Parent is only used if slug=None.

    See docs/extending_cms/api_reference.rst for more info
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
        created_by = get_clean_username(created_by)

    page.urls.create(
        slug=slug,
        path=path,
        page=page,
        managed=not bool(overwrite_url),
        language=language,
    )

    title = Title.objects.create(
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
    title.rescan_placeholders()

    page_languages = page.get_languages()

    if language not in page_languages:
        page.update_languages(page_languages + [language])
    return title


@transaction.atomic
def add_plugin(placeholder, plugin_type, language, position='last-child',
               target=None, **data):
    """
    Add a plugin to a placeholder

    See docs/extending_cms/api_reference.rst for more info
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
            new_pos = target.position + 1
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
                     can_recover_page=True, can_add_pageuser=True,
                     can_change_pageuser=True, can_delete_pageuser=True,
                     can_add_pagepermission=True,
                     can_change_pagepermission=True,
                     can_delete_pagepermission=True, grant_all=False):
    """
    Creates a page user.

    See docs/extending_cms/api_reference.rst for more info
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
        'can_recover_page': can_recover_page,
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
                        can_change_advanced_settings=False, can_publish=False,
                        can_change_permissions=False, can_move_page=False,
                        can_recover_page=True, can_view=False,
                        grant_all=False, global_permission=False):
    """
    Assigns given user to page, and gives him requested permissions.

    See docs/extending_cms/api_reference.rst for more info
    """
    grant_all = grant_all and not global_permission
    data = {
        'can_add': can_add or grant_all,
        'can_change': can_change or grant_all,
        'can_delete': can_delete or grant_all,
        'can_change_advanced_settings': can_change_advanced_settings or grant_all,
        'can_publish': can_publish or grant_all,
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
    Publish a page. This sets `page.published` to `True` and calls publish()
    which does the actual publishing.

    See docs/extending_cms/api_reference.rst for more info
    """
    warnings.warn('This API function has been removed', UserWarning)


def publish_pages(include_unpublished=False, language=None, site=None):
    """
    Create published public version of selected drafts.
    """
    warnings.warn('This API function has been removed', UserWarning)


def get_page_draft(page):
    """
    Returns the draft version of a page, regardless if the passed in
    page is a published version or a draft version.

    :param page: The page to get the draft version
    :type page: :class:`cms.models.pagemodel.Page` instance
    :return page: draft version of the page
    :type page: :class:`cms.models.pagemodel.Page` instance
    """
    warnings.warn('This API function has been removed', UserWarning)


def copy_plugins_to_language(page, source_language, target_language,
                             only_empty=True):
    """
    Copy the plugins to another language in the same page for all the page
    placeholders.

    By default plugins are copied only if placeholder has no plugin for the
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
    """
    from cms.utils import page_permissions

    user = request.user
    current_page = request.current_page

    if current_page:
        return page_permissions.user_can_change_page(user, current_page)

    site = Site.objects.get_current(request)
    return page_permissions.user_can_change_all_pages(user, site)
