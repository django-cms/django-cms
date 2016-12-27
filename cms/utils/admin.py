# -*- coding: utf-8 -*-
import json
from collections import defaultdict

from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.encoding import smart_str

from cms.models import EmptyTitle, Title
from cms.utils import get_language_from_request, get_language_list, get_cms_setting
from cms.utils import page_permissions


NOT_FOUND_RESPONSE = "NotFound"


def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    content = {'status': response.status_code, 'content': smart_str(response.content, response.charset)}
    return HttpResponse(json.dumps(content), content_type="application/json")


def render_admin_rows(request, pages, site, filtered=False, language=None):
    """
    Used for rendering the page tree, inserts into context everything what
    we need for single item
    """
    user = request.user
    site = Site.objects.get_current()
    lang = get_language_from_request(request)
    permissions_on = get_cms_setting('PERMISSION')

    user_can_add = page_permissions.user_can_add_subpage
    user_can_move = page_permissions.user_can_move_page
    user_can_change = page_permissions.user_can_change_page
    user_can_change_advanced_settings = page_permissions.user_can_change_page_advanced_settings
    user_can_publish = page_permissions.user_can_publish_page

    template = get_template('admin/cms/page/tree/menu.html')

    if not language:
        language = get_language_from_request(request)

    filtered = filtered or request.GET.get('q')

    if filtered:
        # When the tree is filtered, it's displayed as a flat structure
        # therefore there's no concept of open nodes.
        open_nodes = []
    else:
        open_nodes = list(map(int, request.GET.getlist('openNodes[]')))

    languages = get_language_list(site.pk)

    page_ids = []

    for page in pages:
        page_ids.append(page.pk)

        if page.publisher_public_id:
            page_ids.append(page.publisher_public_id)

    cms_title_cache = defaultdict(dict)

    cms_page_titles = Title.objects.filter(
        page__in=page_ids,
        language__in=languages
    )

    for cms_title in cms_page_titles.iterator():
        cms_title_cache[cms_title.page_id][cms_title.language] = cms_title

    def render_page_row(page):
        page_cache = cms_title_cache[page.pk]

        for language in languages:
            page_cache.setdefault(language, EmptyTitle(language=language))

        page.title_cache = cms_title_cache[page.pk]

        if page.publisher_public_id:
            publisher_cache = cms_title_cache[page.publisher_public_id]

            for language in languages:
                publisher_cache.setdefault(language, EmptyTitle(language=language))
            page.publisher_public.title_cache = publisher_cache

        has_move_page_permission = user_can_move(user, page)

        metadata = ""

        if permissions_on and not has_move_page_permission:
            # jstree metadata generator
            md = [('valid_children', False), ('draggable', False)]
            # just turn it into simple javascript object
            metadata = "{" + ", ".join(map(lambda e: "%s: %s" % (e[0],
            isinstance(e[1], bool) and str(e[1]) or e[1].lower() ), md)) + "}"

        if filtered:
            children = page.children.none()
        else:
            children = page.get_children()

        context = {
            'request': request,
            'page': page,
            'site': site,
            'lang': lang,
            'filtered': filtered,
            'metadata': metadata,
            'page_languages': page.get_languages(),
            'preview_language': lang,
            'has_add_page_permission': user_can_add(user, target=page),
            'has_change_permission': user_can_change(user, page),
            'has_change_advanced_settings_permission': user_can_change_advanced_settings(user, page),
            'has_publish_permission': user_can_publish(user, page),
            'has_move_page_permission': has_move_page_permission,
            'children': children,
            'site_languages': languages,
            'open_nodes': open_nodes,
            'cms_current_site': site,
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET)
        }
        return template.render(context)

    rendered = (render_page_row(page) for page in pages)
    return ''.join(rendered)
