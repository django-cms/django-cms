# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from django.contrib.sites.models import Site

from cms.models.pagemodel import Page
from cms.models.permissionmodels import GlobalPagePermission
from cms.utils import permissions, moderator, get_language_from_request

NOT_FOUND_RESPONSE = "NotFound"


def get_admin_menu_item_context(request, page, filtered=False):
    """
    Used for rendering the page tree, inserts into context everything what
    we need for single item
    """
    has_add_page_permission = page.has_add_permission(request)
    has_move_page_permission = page.has_move_page_permission(request)
    
    site = Site.objects.get_current()
    lang = get_language_from_request(request)
    #slug = page.get_slug(language=lang, fallback=True) # why was this here ??
    metadata = ""
    if settings.CMS_PERMISSION:
        # jstree metadata generator 
        md = []
        
        #if not has_add_page_permission:
        if not has_move_page_permission:
            md.append(('valid_children', False))
            md.append(('draggable', False))
        if md:
            # just turn it into simple javasript object
            metadata = "{" + ", ".join(map(lambda e: "%s: %s" %(e[0], 
                isinstance(e[1], bool) and str(e[1]) or e[1].lower() ), md)) + "}"
        
    moderator_state = moderator.page_moderator_state(request, page)
    has_add_on_same_level_permission = False
    opts = Page._meta
    if settings.CMS_PERMISSION:
        if (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and
                GlobalPagePermission.objects.with_user(request.user).filter(can_add=True, sites__in=[page.site_id])):
                has_add_on_same_level_permission = True
        
    if not has_add_on_same_level_permission and page.parent_id:
        has_add_on_same_level_permission = permissions.has_generic_permission(page.parent_id, request.user, "add", page.site)
    #has_add_on_same_level_permission = has_add_page_on_same_level_permission(request, page)
    context = {
        'page': page,
        'site': site,
        'lang': lang,
        'filtered': filtered,
        'metadata': metadata,
        
        'has_change_permission': page.has_change_permission(request),
        'has_publish_permission': page.has_publish_permission(request),
        'has_delete_permission': page.has_delete_permission(request),
        'has_move_page_permission': has_move_page_permission,
        'has_add_page_permission': has_add_page_permission,
        'has_moderate_permission': page.has_moderate_permission(request),
        'page_moderator_state': moderator_state,
        'moderator_should_approve': moderator_state['state'] >= moderator.I_APPROVE,
        'has_add_on_same_level_permission': has_add_on_same_level_permission,
        'CMS_PERMISSION': settings.CMS_PERMISSION,
        'CMS_MODERATOR': settings.CMS_MODERATOR,
    }
    return context


def render_admin_menu_item(request, page, template=None):
    """
    Renders requested page item for the tree. This is used in case when item
    must be reloaded over ajax.
    """
    if not template:
        template = "admin/cms/page/menu_item.html"

    if not page.pk:
        return HttpResponse(NOT_FOUND_RESPONSE) # Not found - tree will remove item
        
    # languages
    languages = []
    if page.site_id in settings.CMS_SITE_LANGUAGES:
        languages = settings.CMS_SITE_LANGUAGES[page.site_id]
    else:
        languages = [x[0] for x in settings.CMS_LANGUAGES]
    
    context = RequestContext(request, {
        'has_add_permission': permissions.has_page_add_permission(request),
        'site_languages': languages,
    })
    
    filtered = 'filtered' in request.REQUEST
    context.update(get_admin_menu_item_context(request, page, filtered))
    return render_to_response(template, context)
