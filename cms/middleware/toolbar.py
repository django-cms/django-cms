# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.cms_toolbar import CMSToolbar
from cms.utils.urlutils import is_media_request
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.static import serve

HTML_TYPES = ('text/html', 'application/xhtml+xml')

def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    data = {
        'instance': instance,
        'rendered_content': rendered_content
    }
    return render_to_string('cms/toolbar/placeholder_wrapper.html', data)

try:
    ADMIN_BASE = reverse("admin:index")
except NoReverseMatch:
    ADMIN_BASE = None

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def show_toolbar(self, request):
        if getattr(request, 'view_func', None) is serve:
            return False
        if request.is_ajax():
            return False
        if ADMIN_BASE and request.path.startswith(ADMIN_BASE):
            return False
        if is_media_request(request):
            return False
        if not hasattr(request, "user"):
            return False
        return True

    def process_request(self, request):
        if self.show_toolbar(request):
            request.toolbar = CMSToolbar()
            response = request.toolbar.request_hook(request)
            if isinstance(response, HttpResponse):
                return response