"""
Public Python API to create CMS contents.

WARNING: None of the functions defined in this module checks for permissions.
You must implement the necessary permission checks in your own code before
calling these methods!
"""
import datetime

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import FieldError, PermissionDenied, ValidationError
from django.db import transaction
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.utils.translation import activate

from cms import constants
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models.pagemodel import Page
from cms.models.permissionmodels import ACCESS_PAGE_AND_DESCENDANTS, GlobalPagePermission, PagePermission, PageUser
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils import copy_plugins, get_current_site
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_list
from cms.utils.page import get_available_slug
from cms.utils.permissions import _thread_locals, current_user
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
            print(apphook_pool.apps.values())
            raise
        apphook_name = apphook.__class__.__name__
    elif hasattr(apphook, '__module__') and issubclass(apphook, CMSApp):
        return apphook.__name__
    elif isinstance(apphook, str):
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
                navigation_extenders=None, published=False, site=None,
                login_required=False, limit_visibility_in_menu=constants.VISIBILITY_ALL,
                position="last-child", overwrite_url=None,
                xframe_options=Page.X_FRAME_OPTIONS_INHERIT, page_title=None):
    """
    Create a CMS Page and it's title for the given language

    See docs/extending_cms/api_reference.rst for more info
    """
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
        assert parent.publisher_is_draft

    # validate publication date
    if publication_date:
        assert isinstance(publication_date, datetime.date)

    # validate publication end date
    if publication_end_date:
        assert isinstance(publication_end_date, datetime.date)

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
        created_by = getattr(created_by, get_user_model().USERNAME_FIELD)
    else:
        _thread_locals.user = None

    if reverse_id:
        if Page.objects.drafts().filter(reverse_id=reverse_id, node__site=site).exists():
            raise FieldError('A page with the reverse_id="%s" already exist.' % reverse_id)

    page = Page(
        created_by=created_by,
        changed_by=created_by,
        publication_date=publication_date,
        publication_end_date=publication_end_date,
        in_navigation=in_navigation,
        soft_root=soft_root,
        reverse_id=reverse_id,
        navigation_extenders=navigation_extenders,
        template=template,
        application_urls=application_urls,
        application_namespace=apphook_namespace,
        login_required=login_required,
        limit_visibility_in_menu=limit_visibility_in_menu,
        xframe_options=xframe_options,
    )
    page.set_tree_node(site=site, target=target_node, position=position)
    page.save()
    page.rescan_placeholders()

    create_title(
        language=language,
        title=title,
        page_title=page_title,
        menu_title=menu_title,
        slug=slug,
        redirect=redirect,
        meta_description=meta_description,
        page=page,
        overwrite_url=overwrite_url,
    )

    if published:
        page.publish(language)

    if parent and position in ('last-child', 'first-child'):
        parent._clear_node_cache()

    del _thread_locals.user
    return page


@transaction.atomic
def create_title(language, title, page, menu_title=None, slug=None,
                 redirect=None, meta_description=None, parent=None,
                 overwrite_url=None, page_title=None, path=None):
    """
    Create a title.

    Parent is only used if slug=None.

    See docs/extending_cms/api_reference.rst for more info
    """
    # validate page
    assert isinstance(page, Page)

    # validate language:
    assert language in get_language_list(page.node.site_id)

    # set default slug:
    if not slug:
        base = page.get_path_for_slug(slugify(title), language)
        slug = get_available_slug(page.node.site, base, language)

    if overwrite_url:
        path = overwrite_url.strip('/')
    elif path is None:
        path = page.get_path_for_slug(slug, language)

    title = Title.objects.create(
        language=language,
        title=title,
        menu_title=menu_title,
        page_title=page_title,
        slug=slug,
        path=path,
        redirect=redirect,
        meta_description=meta_description,
        page=page,
        has_url_overwrite=bool(overwrite_url),
    )

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
            if CMSPlugin.node_order_by:
                position = 'sorted-child'
            new_pos = CMSPlugin.objects.filter(parent=target).count()
            parent_id = target.pk
        elif position == 'first-child':
            new_pos = 0
            if CMSPlugin.node_order_by:
                position = 'sorted-child'
            parent_id = target.pk
        elif position == 'left':
            new_pos = target.position
            if CMSPlugin.node_order_by:
                position = 'sorted-sibling'
            parent_id = target.parent_id
        elif position == 'right':
            new_pos = target.position + 1
            if CMSPlugin.node_order_by:
                position = 'sorted-sibling'
            parent_id = target.parent_id
        else:
            raise Exception('position not supported: %s' % position)
        if position == 'last-child' or position == 'first-child':
            qs = CMSPlugin.objects.filter(language=language, parent=target, position__gte=new_pos,
                                          placeholder=placeholder)
        else:
            qs = CMSPlugin.objects.filter(language=language, parent=target.parent_id, position__gte=new_pos,
                                          placeholder=placeholder)
        for pl in qs:
            pl.position += 1
            pl.save()
    else:
        if position == 'last-child':
            new_pos = CMSPlugin.objects.filter(language=language, parent__isnull=True, placeholder=placeholder).count()
        else:
            new_pos = 0
            for pl in CMSPlugin.objects.filter(language=language, parent__isnull=True, position__gte=new_pos,
                                               placeholder=placeholder):
                pl.position += 1
                pl.save()
        parent_id = None
    plugin_base = CMSPlugin(
        plugin_type=plugin_type,
        placeholder=placeholder,
        position=new_pos,
        language=language,
        parent_id=parent_id,
    )

    plugin_base = plugin_base.add_root(instance=plugin_base)

    if target:
        plugin_base = plugin_base.move(target, pos=position)
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
    page = page.reload()

    if not page.has_publish_permission(user):
        raise PermissionDenied()
    # Set the current_user to have the page's changed_by
    # attribute set correctly.
    # 'user' is a user object, but current_user() just wants the username (a string).
    with current_user(user.get_username()):
        page.publish(language)
    return page.reload()


def publish_pages(include_unpublished=False, language=None, site=None):
    """
    Create published public version of selected drafts.
    """
    qs = Page.objects.drafts()

    if not include_unpublished:
        qs = qs.filter(title_set__published=True).distinct()

    if site:
        qs = qs.filter(node__site=site)

    output_language = None
    for i, page in enumerate(qs):
        add = True
        titles = page.title_set
        if not include_unpublished:
            titles = titles.filter(published=True)
        for lang in titles.values_list("language", flat=True):
            if language is None or lang == language:
                if not output_language:
                    output_language = lang
                if not page.publish(lang):
                    add = False
        # we may need to activate the first (main) language for proper page title rendering
        activate(output_language)
        yield (page, add)


def get_page_draft(page):
    """
    Returns the draft version of a page, regardless if the passed in
    page is a published version or a draft version.

    :param page: The page to get the draft version
    :type page: :class:`cms.models.pagemodel.Page` instance
    :return page: draft version of the page
    :type page: :class:`cms.models.pagemodel.Page` instance
    """
    if page:
        if page.publisher_is_draft:
            return page
        else:
            return page.publisher_public
    else:
        return None


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
    placeholders = page.get_placeholders()
    for placeholder in placeholders:
        # only_empty is True we check if the placeholder already has plugins and
        # we skip it if has some
        if not only_empty or not placeholder.get_plugins(language=target_language).exists():
            plugins = list(
                placeholder.get_plugins(language=source_language).order_by('path'))
            copied_plugins = copy_plugins.copy_plugins_to(plugins, placeholder, target_language)
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
