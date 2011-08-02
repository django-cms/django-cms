# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.cms_toolbar import CMSToolbar
from django.http import HttpResponse
from django.template.loader import render_to_string


def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    original_context.push()
    data = {
        'instance': instance,
        'rendered_content': rendered_content
    }
    original_context.update(data)
    output = render_to_string('cms/toolbar/placeholder_wrapper.html', original_context)
    original_context.pop()
    return output

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def process_request(self, request):
        """
        If we should show the toolbar for this request, put it on
        request.toolbar. Then call the request_hook on the toolbar.
        """
        if 'edit' in request.GET and not request.session.get('cms_edit', False):
            request.session['cms_edit'] = True
        request.toolbar = CMSToolbar(request)

    def process_view(self, request, view_func, view_args, view_kwarg):
        response = request.toolbar.request_hook()
        if isinstance(response, HttpResponse):
            return response

