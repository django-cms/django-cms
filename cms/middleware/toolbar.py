# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.plugin_pool import plugin_pool
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.compat.dj import force_unicode
from django.http import HttpResponse
from django.template.loader import render_to_string
from cms.utils.placeholder import get_toolbar_plugin_struct


def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    original_context.push()
    child_plugin_classes = []
    plugin_class = instance.get_plugin_class()
    if plugin_class.allow_children:
        instance, plugin = instance.get_plugin_instance()
        page = original_context['request'].current_page
        childs = [plugin_pool.get_plugin(cls) for cls in plugin.get_child_classes(placeholder, page)]
        # Builds the list of dictionaries containing module, name and value for the plugin dropdowns
        child_plugin_classes = get_toolbar_plugin_struct(childs, placeholder.slot, placeholder.page, parent=plugin_class)
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
            if request.session.get('cms_build', False):
                request.session['cms_build'] = False
        if 'edit_off' in request.GET and request.session.get('cms_edit', True):
            request.session['cms_edit'] = False
            if request.session.get('cms_build', False):
                request.session['cms_build'] = False
        if 'build' in request.GET and not request.session.get('cms_build', False):
            request.session['cms_build'] = True
        request.toolbar = CMSToolbar(request)

    def process_view(self, request, view_func, view_args, view_kwarg):
        response = request.toolbar.request_hook()
        if isinstance(response, HttpResponse):
            return response

