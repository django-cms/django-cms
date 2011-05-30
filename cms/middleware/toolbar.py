# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.cms_toolbar import CMSToolbar
from django.http import HttpResponse
from django.template.loader import render_to_string


def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    data = {
        'instance': instance,
        'rendered_content': rendered_content
    }
    return render_to_string('cms/toolbar/placeholder_wrapper.html', data)

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def process_request(self, request):
        """
        If we should show the toolbar for this request, put it on
        request.toolbar. Then call the request_hook on the toolbar.
        """
        if 'edit' in request.GET:
            request.session['cms_edit'] = True
        request.toolbar = CMSToolbar()
        response = request.toolbar.request_hook(request)
        if isinstance(response, HttpResponse):
            return response