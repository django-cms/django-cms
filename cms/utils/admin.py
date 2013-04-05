# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils import simplejson
from django.contrib.sites.models import Site

from cms.models import Page
from cms.utils import permissions, moderator, get_language_from_request, get_language_list, get_cms_setting
from cms.utils.permissions import has_global_page_permission

NOT_FOUND_RESPONSE = "NotFound"

def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    return HttpResponse(simplejson.dumps({'status':response.status_code,'content':response.content}),
                                content_type="application/json")

publisher_classes = {
    Page.PUBLISHER_STATE_DIRTY: "publisher_dirty",
    Page.PUBLISHER_STATE_PENDING: "publisher_pending",
}

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
    if get_cms_setting('PERMISSION'):
        # jstree metadata generator 
        md = []
        
        #if not has_add_page_permission:
        if not has_move_page_permission:
            md.append(('valid_children', False))
            md.append(('draggable', False))
        if md:
            # just turn it into simple javascript object
            metadata = "{" + ", ".join(map(lambda e: "%s: %s" %(e[0], 
                isinstance(e[1], bool) and str(e[1]) or e[1].lower() ), md)) + "}"
        
    has_add_on_same_level_permission = False
    opts = Page._meta
    if get_cms_setting('PERMISSION'):
        perms = has_global_page_permission(request, page.site_id, can_add=True)
        if (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and perms):
            has_add_on_same_level_permission = True

    if page.delete_requested():
        css_class = "publisher_delete_requested"
    elif not page.published:
        css_class = "publisher_draft"
    else:
        css_class = publisher_classes.get(page.publisher_state, "")

    if not has_add_on_same_level_permission and page.parent_id:
        has_add_on_same_level_permission = permissions.has_generic_permission(page.parent_id, request.user, "add", page.site)
    #has_add_on_same_level_permission = has_add_page_on_same_level_permission(request, page)
    context = {
        'page': page,
        'site': site,
        'lang': lang,
        'filtered': filtered,
        'metadata': metadata,
        'css_class': css_class,
        
        'has_change_permission': page.has_change_permission(request),
        'has_publish_permission': page.has_publish_permission(request),
        'has_delete_permission': page.has_delete_permission(request),
        'has_move_page_permission': has_move_page_permission,
        'has_add_page_permission': has_add_page_permission,
        'has_add_on_same_level_permission': has_add_on_same_level_permission,
        'CMS_PERMISSION': get_cms_setting('PERMISSION'),
        'CMS_SHOW_END_DATE': get_cms_setting('SHOW_END_DATE'),
    }
    return context


def render_admin_menu_item(request, page, template=None):
    """
    Renders requested page item for the tree. This is used in case when item
    must be reloaded over ajax.
    """
    if not template:
        template = "admin/cms/page/menu_fragment.html"

    if not page.pk:
        return HttpResponse(NOT_FOUND_RESPONSE) # Not found - tree will remove item
        
    # languages
    languages = get_language_list(page.site_id)
    context = RequestContext(request, {
        'has_add_permission': permissions.has_page_add_permission(request),
        'site_languages': languages,
    })
    
    filtered = 'filtered' in request.REQUEST
    context.update(get_admin_menu_item_context(request, page, filtered))
    # add mimetype to help out IE
    return render_to_response(template, context, mimetype="text/html; charset=utf-8")
