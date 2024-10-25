from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import Resolver404, resolve, reverse

from cms import __version__, constants
from cms.cache.page import set_page_cache
from cms.models import EmptyPageContent
from cms.utils.page_permissions import user_can_change_page, user_can_view_page


def render_page(request, page, current_language, slug=None):
    """
    Renders a page
    """
    page_content = page.page_content_cache.get(current_language, page.get_content_obj(current_language))
    context = {}
    context['lang'] = current_language
    context['current_page'] = page
    context['current_pagecontent'] = page_content
    context['has_change_permissions'] = user_can_change_page(request.user, page)
    context['has_view_permissions'] = user_can_view_page(request.user, page)

    cant_view_page = any([
        not context['has_view_permissions'],
        isinstance(page_content, EmptyPageContent)
    ])
    if cant_view_page:
        return _handle_no_page(request)

    template = page_content.get_template()
    response = TemplateResponse(request, template, context)
    response.add_post_render_callback(set_page_cache)

    # Add headers for X Frame Options - this really should be changed upon moving to class based views
    xframe_options = page.get_xframe_options()
    # xframe_options can be None if there's no xframe information on the page
    # (eg. a top-level page which has xframe options set to "inherit")
    if xframe_options == constants.X_FRAME_OPTIONS_INHERIT or xframe_options is None:
        # This is when we defer to django's own clickjacking handling
        return response

    # We want to prevent django setting this in their middleware
    response.xframe_options_exempt = True

    if xframe_options == constants.X_FRAME_OPTIONS_ALLOW:
        # Do nothing, allowed is no header.
        return response
    elif xframe_options == constants.X_FRAME_OPTIONS_SAMEORIGIN:
        response['X-Frame-Options'] = 'SAMEORIGIN'
    elif xframe_options == constants.X_FRAME_OPTIONS_DENY:
        response['X-Frame-Options'] = 'DENY'
    return response


def _handle_no_page(request):
    try:
        # redirect to PageContent's changelist if the root page is detected
        resolved_path = resolve(request.path)
        if resolved_path.url_name == 'pages-root':
            redirect_url = reverse('admin:cms_pagecontent_changelist')
            return HttpResponseRedirect(redirect_url)

        # add a $ to the end of the url (does not match on the cms anymore)
        resolve('%s$' % request.path)
    except Resolver404 as e:
        # raise a django http 404 page
        exc = Http404(dict(path=request.path, tried=e.args[0]['tried']))
        raise exc
    raise Http404('CMS Page not found: %s' % request.path)


def _handle_no_apphook(request):
    context = {
        "absolute_url": request.toolbar.request_path,
    }
    return TemplateResponse(request, "cms/noapphook.html", context)


def _render_welcome_page(request):
    context = {
        'cms_version': __version__,
        'django_debug': settings.DEBUG,
        'next_url': reverse('pages-root'),
    }
    return TemplateResponse(request, "cms/welcome.html", context)


def render_pagecontent(request, pagecontent):
    language = pagecontent.language
    request.current_page = page = pagecontent.page
    page.page_content_cache[language] = pagecontent
    return render_page(request, page, language)
