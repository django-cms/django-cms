from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import Resolver404, resolve, reverse

from cms import __version__
from cms.cache.page import set_page_cache
from cms.models import Page
from cms.utils.conf import get_cms_setting
from cms.utils.page import get_page_template_from_request
from cms.utils.page_permissions import user_can_change_page, user_can_view_page


def render_page(request, page, current_language, slug):
    """
    Renders a page
    """
    context = {}
    context['lang'] = current_language
    context['current_page'] = page
    context['has_change_permissions'] = user_can_change_page(request.user, page)
    context['has_view_permissions'] = user_can_view_page(request.user, page)

    if not context['has_view_permissions']:
        return _handle_no_page(request)

    template = get_page_template_from_request(request)
    response = TemplateResponse(request, template, context)
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


def render_object_structure(request, obj):
    context = {
        'object': obj,
        'cms_toolbar': request.toolbar,
    }
    return render(request, 'cms/toolbar/structure.html', context)


def _handle_no_page(request):
    try:
        #add a $ to the end of the url (does not match on the cms anymore)
        resolve('%s$' % request.path)
    except Resolver404 as e:
        # raise a django http 404 page
        exc = Http404({"path": request.path, "tried": e.args[0]['tried']})
        raise exc
    raise Http404('CMS Page not found: %s' % request.path)


def _render_welcome_page(request):
    context = {
        'cms_version': __version__,
        'cms_edit_on': get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'),
        'django_debug': settings.DEBUG,
        'next_url': reverse('pages-root'),
    }
    return TemplateResponse(request, "cms/welcome.html", context)
