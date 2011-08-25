# -*- coding: utf-8 -*-
"""
Public Python API to create CMS contents.

WARNING: None of the functions defined in this module checks for permissions.
You must implement the necessary permission checks in your own code before
calling these methods!
"""
import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models import Max
from django.template.defaultfilters import slugify
from menus.menu_pool import menu_pool

from cms.admin.forms import save_permissions
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.models.moderatormodels import ACCESS_PAGE_AND_DESCENDANTS
from cms.models.pagemodel import Page
from cms.models.permissionmodels import PageUser, PagePermission, GlobalPagePermission
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils import moderator
from cms.utils.permissions import _thread_locals


#===============================================================================
# Constants 
#===============================================================================

VISIBILITY_ALL = None
VISIBILITY_USERS = 1
VISIBILITY_STAFF = 2

#===============================================================================
# Helpers/Internals
#===============================================================================

def _generate_valid_slug(source, parent, language):
    """
    Generate a valid slug for a page from source for the given language.
    Parent is passed so we can make sure the slug is unique for this level in
    the page tree.
    """
    if parent:
        qs = Title.objects.filter(language=language, page__parent=parent)
    else:
        qs = Title.objects.filter(language=language, page__parent__isnull=True)
    used = qs.values_list('slug', flat=True)
    baseslug = slugify(source)
    slug = baseslug
    i = 1
    while slug in used:
        slug = '%s-%s' % (baseslug, i)
        i += 1
    return slug

def _verify_apphook(apphook):
    """
    Verifies the apphook given is valid and returns the normalized form (name)
    """
    if hasattr(apphook, '__module__') and  issubclass(apphook, CMSApp):
        apphook_pool.discover_apps()
        assert apphook in apphook_pool.apps.values()
        return apphook.__name__
    elif isinstance(apphook, basestring):
        apphook_pool.discover_apps()
        assert apphook in apphook_pool.apps
        return apphook
    else:
        raise TypeError("apphook must be string or CMSApp instance")

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
    elif isinstance(plugin_type, basestring):
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

def create_page(title, template, language, menu_title=None, slug=None,
                apphook=None, redirect=None, meta_description=None,
                meta_keywords=None, created_by='python-api', parent=None,
                publication_date=None, publication_end_date=None,
                in_navigation=False, soft_root=False, reverse_id=None,
                navigation_extenders=None, published=False, site=None,
                login_required=False, limit_visibility_in_menu=VISIBILITY_ALL,
                position="last-child", overwrite_url=None):
    """
    Create a CMS Page and it's title for the given language
    
    See docs/extending_cms/api_reference.rst for more info
    """
    # ugly permissions hack
    if created_by and isinstance(created_by, User):
        _thread_locals.user = created_by
        created_by = created_by.username
    else:
        _thread_locals.user = None
    
    # validate template
    assert template in [tpl[0] for tpl in settings.CMS_TEMPLATES]
    
    # validate language:
    assert language in [lang[0] for lang in settings.CMS_LANGUAGES]
    
    # set default slug:
    if not slug:
        slug = _generate_valid_slug(title, parent, language)
    
    # validate and normalize apphook 
    if apphook:
        application_urls = _verify_apphook(apphook)
    else:
        application_urls = None
    
    # validate parent
    if parent:
        assert isinstance(parent, Page)
    
    # validate publication date
    if publication_date:
        assert isinstance(publication_date, datetime.date)
    
    # validate publication end date
    if publication_end_date:
        assert isinstance(publication_end_date, datetime.date)
        
    # validate softroot
    assert settings.CMS_SOFTROOT or not soft_root
    
    # validate site
    if not site:
        site = Site.objects.get_current()
    else:
        assert isinstance(site, Site)
        
    if navigation_extenders:
        raw_menus = menu_pool.get_menus_by_attribute("cms_enabled", True)
        menus = [menu[0] for menu in raw_menus]
        assert navigation_extenders in menus
        
    # validate menu visibility
    accepted_limitations = (VISIBILITY_ALL, VISIBILITY_USERS, VISIBILITY_STAFF)
    assert limit_visibility_in_menu in accepted_limitations
    
    # validate position
    assert position in ('last-child', 'first-child', 'left', 'right')
    
    page = Page(
        created_by=created_by,
        changed_by=created_by,
        parent=parent,
        publication_date=publication_date,
        publication_end_date=publication_end_date,
        in_navigation=in_navigation,
        soft_root=soft_root,
        reverse_id=reverse_id,
        navigation_extenders=navigation_extenders,
        published=published,
        template=template,
        site=site,
        login_required=login_required,
        limit_visibility_in_menu=limit_visibility_in_menu,
    )
    if parent:
        page.insert_at(parent, position)
    page.save()

    if settings.CMS_MODERATOR and _thread_locals.user:
        page.pagemoderator_set.create(user=_thread_locals.user)
    
    create_title(
        language=language,
        title=title,
        menu_title=menu_title,
        slug=slug,
        apphook=application_urls,
        redirect=redirect,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        page=page,
        overwrite_url=overwrite_url
    )
        
    del _thread_locals.user
    return page
    
def create_title(language, title, page, menu_title=None, slug=None,
                 apphook=None, redirect=None, meta_description=None,
                 meta_keywords=None, parent=None, overwrite_url=None):
    """
    Create a title.
    
    Parent is only used if slug=None.
    
    See docs/extending_cms/api_reference.rst for more info
    """
    # validate language:
    assert language in [lang[0] for lang in settings.CMS_LANGUAGES]
    
    # validate page
    assert isinstance(page, Page)
    
    # set default slug:
    if not slug:
        slug = _generate_valid_slug(title, parent, language)
        
    # validate and normalize apphook 
    if apphook:
        application_urls = _verify_apphook(apphook)
    else:
        application_urls = None
    
    title = Title.objects.create(
        language=language,
        title=title,
        menu_title=menu_title,
        slug=slug,
        application_urls=application_urls,
        redirect=redirect,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        page=page
    )

    if overwrite_url:
        title.has_url_overwrite = True
        title.path = overwrite_url
        title.save()

    return title

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
        

    max_pos = CMSPlugin.objects.filter(language=language,
        placeholder=placeholder).aggregate(Max('position'))['position__max'] or 0

    plugin_base = CMSPlugin(
        plugin_type=plugin_type,
        placeholder=placeholder, 
        position=max_pos + 1,
        language=language
    )
    plugin_base.insert_at(target, position=position, save=False)
            
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
    if grant_all:
        # just be lazy
        return create_page_user(created_by, user, True, True, True, True,
                                True, True, True, True, True, True, True)
    
    # validate created_by
    assert isinstance(created_by, User)
    
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
    for field in [f.name for f in User._meta.local_fields]:
        setattr(page_user, field, getattr(user, field))
    user.save()
    page_user.save()
    save_permissions(data, page_user)
    return user
        
def assign_user_to_page(page, user, grant_on=ACCESS_PAGE_AND_DESCENDANTS,
    can_add=False, can_change=False, can_delete=False, 
    can_change_advanced_settings=False, can_publish=False, 
    can_change_permissions=False, can_move_page=False, can_moderate=False, 
    can_recover_page=True, can_view=False,
    grant_all=False, global_permission=False):
    """
    Assigns given user to page, and gives him requested permissions.
    
    See docs/extending_cms/api_reference.rst for more info
    """
    if grant_all and not global_permission:
        # shortcut to grant all permissions
        return assign_user_to_page(page, user, grant_on, True, True, True, True,
                                   True, True, True, True, True)
    
    data = {
        'can_add': can_add,
        'can_change': can_change,
        'can_delete': can_delete, 
        'can_change_advanced_settings': can_change_advanced_settings,
        'can_publish': can_publish, 
        'can_change_permissions': can_change_permissions, 
        'can_move_page': can_move_page, 
        'can_moderate': can_moderate,  
        'can_view': can_view,
    }
    page_permission = PagePermission(page=page, user=user,
                                     grant_on=grant_on, **data)
    page_permission.save()
    if global_permission:
        page_permission = GlobalPagePermission(
            user=user, can_recover_page=can_recover_page, **data)
        page_permission.save()
        page_permission.sites.add(Site.objects.get_current())
    return page_permission
    
def publish_page(page, user, approve=False):
    """
    Publish a page. This sets `page.published` to `True` and saves it, which
    triggers `cms.utils.moderator.page_changed` which does the actual moderation
    and publishing action.
    
    See docs/extending_cms/api_reference.rst for more info
    """
    page.published = True
    # the magic happens in the post save signal here... WTF?
    page.save()
    # reload page
    page = Page.objects.get(pk=page.pk)
    # approve page if requested
    if approve:
        page = approve_page(page, user)
    return page.reload()
    
def approve_page(page, user):
    """
    Approve a page version.
    
    See docs/extending_cms/api_reference.rst for more info
    """
    class FakeRequest(object):
        def __init__(self, user):
            self.user = user
    request = FakeRequest(user)
    moderator.approve_page(request, page)
    return Page.objects.get(pk=page.pk)
