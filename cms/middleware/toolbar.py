# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.cms_toolbar import CMSToolbar
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponse
from django.template.context import RequestContext
from django.template.loader import render_to_string
import re
import warnings

HTML_TYPES = ('text/html', 'application/xhtml+xml')

try:
    ADMIN_BASE = reverse("admin:index")
except NoReverseMatch:
    ADMIN_BASE = None

BODY_RE = re.compile(r'<body.*?>', re.IGNORECASE)
BACKWARDS_COMPAT_TEMPLATE = template.Template(
    "{% load cms_tags %}{{ pre|safe }}{% cms_toolbar %}{{ post|safe }}"
)

def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    data = {
        'instance': instance,
        'rendered_content': rendered_content
    }
    return render_to_string('cms/toolbar/placeholder_wrapper.html', data)

def _patch(data, request):
    match = BODY_RE.search(data)
    if not match:
        return data
    warnings.warn("You have to use the {% cms_toolbar %} tag in your templates "
                  "if you use the cms.middleware.toolbar.ToolbarMiddleware.",
                  DeprecationWarning)
    end = match.end()
    ctx = RequestContext(request)
    ctx['pre'] = data[:end]
    ctx['post'] = data[end:]
    return BACKWARDS_COMPAT_TEMPLATE.render(ctx)

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def should_show_toolbar(self, request):
        """
        Check if we should show the toolbar for this request or not.
        """
        if ADMIN_BASE and request.path.startswith(ADMIN_BASE):
            return False
        # check session
        if request.session.get('cms_edit', False):
            return True
        # check GET
        if 'edit' in request.GET:
            request.session['cms_edit'] = True
            return True
        return False

    def process_request(self, request):
        """
        If we should show the toolbar for this request, put it on
        request.toolbar. Then call the request_hook on the toolbar.
        """
        if self.should_show_toolbar(request):
            request.toolbar = CMSToolbar(request)
            response = request.toolbar.request_hook()
            if isinstance(response, HttpResponse):
                return response
    
    def process_response(self, request, response):
        """
        For backwards compatibility, will be removed in 2.3
        """
        
        if not getattr(request, 'toolbar', False):
            return response
        if getattr(request, '_cms_toolbar_tag_used', False):
            return response
        if not response['Content-Type'].startswith(HTML_TYPES):
            return response
        response.content = _patch(response.content, request)
        return response