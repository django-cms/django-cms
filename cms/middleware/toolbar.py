# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.cms_toolbar import CMSToolbar
from cms.utils.urlutils import is_media_request
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponse
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.views.static import serve
import re
import warnings

HTML_TYPES = ('text/html', 'application/xhtml+xml')

try:
    ADMIN_BASE = reverse("admin:index")
except NoReverseMatch:
    ADMIN_BASE = None

BODY_RE = re.compile(r'<body.*?>', re.IGNORECASE)

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
    ctx['CMS_TOOLBAR_CONFIG'] = request.toolbar.as_json({}, request)
    toolbar = render_to_string('cms/toolbar/toolbar.html', ctx)
    return u'%s%s%s' % (data[:end], toolbar, data[end:])

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def show_toolbar(self, request):
        if request.session.get('cms_edit', False):
            return True
        if 'edit' in request.GET:
            return True
        if request.is_ajax():
            return False
        if ADMIN_BASE and request.path.startswith(ADMIN_BASE):
            return False
        if is_media_request(request):
            return False
        if not hasattr(request, "user"):
            return False
        return False

    def process_request(self, request):
        if self.show_toolbar(request):
            request.toolbar = CMSToolbar()
            response = request.toolbar.request_hook(request)
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