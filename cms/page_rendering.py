# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404
from django.http import Http404
from django.template.response import TemplateResponse

from cms import __version__
from cms.cache.page import set_page_cache
from cms.models import Page
from cms.utils import get_template_from_request
from cms.utils.conf import get_cms_setting


def render_page(request, page, current_language, slug):
    """
    Renders a page
    """
    template_name = get_template_from_request(request, page, no_current_page=True)
    # fill the context
    context = {}
    context['lang'] = current_language
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    context['has_view_permissions'] = page.has_view_permission(request)

    if not context['has_view_permissions']:
        return _handle_no_page(request, slug)

    response = TemplateResponse(request, template_name, context)

    response.add_post_render_callback(set_page_cache)

    # Add headers for X Frame Options - this really should be changed upon moving to class based views
    xframe_options = page.get_xframe_options()
    # xframe_options can be None if there's no xframe information on the page
    # (eg. a top-level page which has xframe options set to "inherit")
    if xframe_options == Page.X_FRAME_OPTIONS_INHERIT or xframe_options is None:
        # This is when we defer to django's own clickjacking handling
        return response

    # We want to prevent django setting this in their middlewear
    response.xframe_options_exempt = True

    if xframe_options == Page.X_FRAME_OPTIONS_ALLOW:
        # Do nothing, allowed is no header.
        return response
    elif xframe_options == Page.X_FRAME_OPTIONS_SAMEORIGIN:
        response['X-Frame-Options'] = 'SAMEORIGIN'
    elif xframe_options == Page.X_FRAME_OPTIONS_DENY:
        response['X-Frame-Options'] = 'DENY'
    return response


def _handle_no_page(request, slug):
    context = {}
    context['cms_version'] = __version__
    context['cms_edit_on'] = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')

    if not slug and settings.DEBUG:
        return TemplateResponse(request, "cms/welcome.html", context)
    try:
        #add a $ to the end of the url (does not match on the cms anymore)
        resolve('%s$' % request.path)
    except Resolver404 as e:
        # raise a django http 404 page
        exc = Http404(dict(path=request.path, tried=e.args[0]['tried']))
        raise exc
    raise Http404('CMS Page not found: %s' % request.path)

