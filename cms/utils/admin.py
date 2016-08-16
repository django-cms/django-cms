# -*- coding: utf-8 -*-
import json

from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.utils.encoding import smart_str

from cms.utils import get_language_from_request, get_language_list, get_cms_setting
from cms.utils.page_permissions import user_can_change_page_advanced_settings


NOT_FOUND_RESPONSE = "NotFound"


def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    content = {'status': response.status_code, 'content': smart_str(response.content, response.charset)}
    return HttpResponse(json.dumps(content), content_type="application/json")


def get_admin_menu_item_context(request, page, filtered=False, language=None, restrictions=None):
    """
    Used for rendering the page tree, inserts into context everything what
    we need for single item
    """
    user = request.user
    has_add_page_permission = page.has_add_permission(user)
    has_move_page_permission = page.has_move_page_permission(user)

    site = Site.objects.get_current()
    lang = get_language_from_request(request)

    metadata = ""

    if get_cms_setting('PERMISSION'):
        # jstree metadata generator
        md = []

        if not has_move_page_permission:
            md.append(('valid_children', False))
            md.append(('draggable', False))
        if md:
            # just turn it into simple javascript object
            metadata = "{" + ", ".join(map(lambda e: "%s: %s" % (e[0],
            isinstance(e[1], bool) and str(e[1]) or e[1].lower() ), md)) + "}"

    context = {
        'request': request,
        'page': page,
        'site': site,
        'lang': lang,
        'filtered': filtered,
        'metadata': metadata,
        'preview_language': language,
        'has_change_permission': page.has_change_permission(user),
        'has_change_advanced_settings_permission': user_can_change_page_advanced_settings(user, page),
        'has_publish_permission': page.has_publish_permission(user),
        'has_delete_permission': page.has_delete_permission(user),
        'has_move_page_permission': has_move_page_permission,
        'has_add_page_permission': has_add_page_permission,
        'children': page.children.all(),
        'site_languages': get_language_list(page.site_id),
    }
    return context


def render_admin_menu_item(request, page, template=None, language=None,
                           open_nodes=()):
    """
    Renders requested page item for the tree. This is used in case when item
    must be reloaded over ajax.
    """
    # languages
    context = {
        'open_nodes': open_nodes,
    }
    filtered = 'filtered' in request.GET or 'filtered' in request.POST
    context.update(get_admin_menu_item_context(request, page, filtered, language))
    return render_to_string(template, context)
