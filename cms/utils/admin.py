from django.contrib.sites.models import Site
from django.conf import settings
from cms.utils.moderator import page_moderator_state, I_APPROVE
from cms.utils import get_language_from_request
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from cms.utils.permissions import has_page_add_permission, has_generic_permission
from django.http import HttpResponse
from cms.models.permissionmodels import GlobalPagePermission
from cms.models.pagemodel import Page


def get_admin_menu_item_context(request, page, filtered=False):
    """Used for rendering the page tree, inserts into context everything what
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
        
    moderator_state = page_moderator_state(request, page)
    has_add_on_same_level_permission = False
    opts = Page._meta
    if (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and
            GlobalPagePermission.objects.with_user(request.user).filter(can_add=True, sites__in=[page.site_id])):
            has_add_on_same_level_permission = True
        
    if not has_add_on_same_level_permission and page.parent_id:
        has_add_on_same_level_permission = has_generic_permission(page.parent_id, request.user, "add", page.site)
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
        'moderator_should_approve': moderator_state['state'] >= I_APPROVE,
        
        'has_add_on_same_level_permission': has_add_on_same_level_permission,
        
        'CMS_PERMISSION': settings.CMS_PERMISSION,
        'CMS_MODERATOR': settings.CMS_MODERATOR,
    }
    return context


NOT_FOUND_RESPONSE = "NotFound"

def render_admin_menu_item(request, page):
    """Renders requested page item for the tree. This is used in case when item
    must be reloaded over ajax.
    """
    
    if not page.pk:
        return HttpResponse(NOT_FOUND_RESPONSE) # Not found - tree will remove item
    
    context = RequestContext(request, {
        'has_add_permission': has_page_add_permission(request),
    })
    
    filtered = 'filtered' in request.REQUEST
    context.update(get_admin_menu_item_context(request, page, filtered))
    return render_to_response('admin/cms/page/menu_item.html', context) 