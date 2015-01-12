# -*- coding: utf-8 -*-
import json

from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import smart_str

from cms.constants import PUBLISHER_STATE_PENDING, PUBLISHER_STATE_DIRTY
from cms.models import Page, GlobalPagePermission
from cms.utils import get_language_from_request
from cms.utils import get_language_list
from cms.utils import get_cms_setting
from cms.utils.compat import DJANGO_1_4

NOT_FOUND_RESPONSE = "NotFound"


def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    content = {'status': response.status_code, 'content': smart_str(response.content, response._charset)}
    if DJANGO_1_4:
        return HttpResponse(json.dumps(content), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(content), content_type="application/json")


publisher_classes = {
    PUBLISHER_STATE_DIRTY: "publisher_dirty",
    PUBLISHER_STATE_PENDING: "publisher_pending",
}


def get_admin_menu_item_context(request, page, filtered=False, language=None):
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
            metadata = "{" + ", ".join(map(lambda e: "%s: %s" % (e[0],
            isinstance(e[1], bool) and str(e[1]) or e[1].lower() ), md)) + "}"

    has_add_on_same_level_permission = False
    opts = Page._meta
    if get_cms_setting('PERMISSION'):
        global_add_perm = GlobalPagePermission.objects.user_has_add_permission(
            request.user, page.site_id).exists()
        if request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and global_add_perm:
            has_add_on_same_level_permission = True
    from cms.utils import permissions
    if not has_add_on_same_level_permission and page.parent_id:
        has_add_on_same_level_permission = permissions.has_generic_permission(page.parent_id, request.user, "add",
                                                                              page.site)
        #has_add_on_same_level_permission = has_add_page_on_same_level_permission(request, page)
    context = {
        'page': page,
        'site': site,
        'lang': lang,
        'filtered': filtered,
        'metadata': metadata,
        'preview_language': language,
        'has_change_permission': page.has_change_permission(request),
        'has_publish_permission': page.has_publish_permission(request),
        'has_delete_permission': page.has_delete_permission(request),
        'has_move_page_permission': has_move_page_permission,
        'has_add_page_permission': has_add_page_permission,
        'has_add_on_same_level_permission': has_add_on_same_level_permission,
        'CMS_PERMISSION': get_cms_setting('PERMISSION'),
    }
    return context


def render_admin_menu_item(request, page, template=None, language=None):
    """
    Renders requested page item for the tree. This is used in case when item
    must be reloaded over ajax.
    """
    if not template:
        template = "admin/cms/page/tree/menu_fragment.html"

    if not page.pk:
        return HttpResponse(NOT_FOUND_RESPONSE) # Not found - tree will remove item

    # languages
    from cms.utils import permissions
    languages = get_language_list(page.site_id)
    context = RequestContext(request, {
        'has_add_permission': permissions.has_page_add_permission(request),
        'site_languages': languages,
    })

    filtered = 'filtered' in request.REQUEST
    context.update(get_admin_menu_item_context(request, page, filtered, language))
    # add mimetype to help out IE
    if DJANGO_1_4:
        return render_to_response(template, context, mimetype="text/html; charset=utf-8")
    else:
        return render_to_response(template, context, content_type="text/html; charset=utf-8")
