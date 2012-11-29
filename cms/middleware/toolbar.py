# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.plugin_pool import plugin_pool
from cms.cms_toolbar import CMSToolbar
from django.http import HttpResponse
from django.template.loader import render_to_string


def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    original_context.push()
    child_plugin_classes = []
    if instance.get_plugin_class().allow_children:
        instance, plugin = instance.get_plugin_instance()
        for child_class_name in plugin.get_child_classes(placeholder, original_context['request'].current_page):
            cls = plugin_pool.get_plugin(child_class_name)
            child_plugin_classes.append((cls.__name__, unicode(cls.name)))
    data = {
        'instance': instance,
        'rendered_content': rendered_content,
        'child_plugin_classes': child_plugin_classes,
    }
    original_context.update(data)
    output = render_to_string(instance.get_plugin_class().frontend_edit_template, original_context)
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

