from django.contrib.sites.models import Site
from cms import settings as cms_settings
from cms.utils.moderator import page_moderator_state, I_APPROVE
from cms.utils import get_language_from_request
from django.shortcuts import render_to_response
from django.template.context import RequestContext


def get_admin_menu_item_context(request, page, filtered=False):
    """Used for rendering the page tree, inserts into context everything what
    we need for single item
    """
    has_add_permission = page.has_add_permission(request)
    has_move_page_permission = page.has_move_page_permission(request)
    
    site = Site.objects.get_current()
    lang = get_language_from_request(request)
    
    metadata = ""
    if cms_settings.CMS_PERMISSION:
        # jstree metadata generator 
        md = []
        if not has_add_permission:
            md.append(('valid_children', False))
        if not has_move_page_permission:
            md.append(('draggable', False))
        
        # just turn it into simple javasript object
        metadata = "{" + ", ".join(map(lambda e: "%s: %s" %(e[0], 
            str(e[1]).lower() if isinstance(e[1], bool) else str(e[1])), md)) + "}"
    
    moderator_state = page_moderator_state(request, page)
    
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
        'has_add_page_permission': has_add_permission,
        'has_moderate_permission': page.has_moderate_permission(request),
        'page_moderator_state': moderator_state,
        'moderator_should_approve': moderator_state['state'] is I_APPROVE,
        
        'CMS_PERMISSION': cms_settings.CMS_PERMISSION,
        'CMS_MODERATOR': cms_settings.CMS_MODERATOR,
    }
    return context


def render_admin_menu_item(request, page):
    """Renders requested page item for the tree. This is used in case when item
    must be reloaded over ajax.
    """
    context = RequestContext(request)
    filtered = 'filtered' in request.REQUEST
    
    context.update(get_admin_menu_item_context(request, page, filtered))
    return render_to_response('admin/cms/page/menu_item.html', context) 