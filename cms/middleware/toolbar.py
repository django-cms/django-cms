# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from cms.utils.conf import get_cms_setting
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.i18n import force_language
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from menus.menu_pool import menu_pool
from django.http import HttpResponse
from django.template.loader import render_to_string
from cms.utils.placeholder import get_toolbar_plugin_struct


def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    from cms.plugin_pool import plugin_pool

    original_context.push()
    child_plugin_classes = []
    plugin_class = instance.get_plugin_class()
    if plugin_class.allow_children:
        inst, plugin = instance.get_plugin_instance()
        page = original_context['request'].current_page
        children = [plugin_pool.get_plugin(cls) for cls in plugin.get_child_classes(placeholder, page)]
        # Builds the list of dictionaries containing module, name and value for the plugin dropdowns
        child_plugin_classes = get_toolbar_plugin_struct(children, placeholder.slot, placeholder.page,
                                                         parent=plugin_class)
    instance.placeholder = placeholder
    request = original_context['request']
    with force_language(request.toolbar.toolbar_language):
        data = {
            'instance': instance,
            'rendered_content': rendered_content,
            'child_plugin_classes': child_plugin_classes,
            'edit_url': placeholder.get_edit_url(instance.pk),
            'add_url': placeholder.get_add_url(),
            'delete_url': placeholder.get_delete_url(instance.pk),
            'move_url': placeholder.get_move_url(),
        }
    original_context.update(data)
    plugin_class = instance.get_plugin_class()
    template = plugin_class.frontend_edit_template
    output = render_to_string(template, original_context).strip()
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

        edit_on = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        edit_off = get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        build = get_cms_setting('CMS_TOOLBAR_URL__BUILD')

        if request.user.is_staff or request.user.is_anonymous():
            if edit_on in request.GET and not request.session.get('cms_edit', False):
                if not request.session.get('cms_edit', False):
                    menu_pool.clear()
                request.session['cms_edit'] = True
                if request.session.get('cms_build', False):
                    request.session['cms_build'] = False
            if edit_off in request.GET and request.session.get('cms_edit', True):
                if request.session.get('cms_edit', True):
                    menu_pool.clear()
                request.session['cms_edit'] = False
                if request.session.get('cms_build', False):
                    request.session['cms_build'] = False
            if build in request.GET and not request.session.get('cms_build', False):
                request.session['cms_build'] = True
        else:
            request.session['cms_build'] = False
            request.session['cms_edit'] = False
        if request.user.is_staff:
            try:
                request.cms_latest_entry = LogEntry.objects.filter(
                    user=request.user,
                    action_flag__in=(ADDITION, CHANGE)
                ).only('pk').order_by('-pk')[0].pk
            except IndexError:
                request.cms_latest_entry = -1
        request.toolbar = CMSToolbar(request)

    def process_view(self, request, view_func, view_args, view_kwarg):
        response = request.toolbar.request_hook()
        if isinstance(response, HttpResponse):
            return response

    def process_response(self, request, response):
        from django.utils.cache import add_never_cache_headers

        found = False
        if hasattr(request, 'toolbar') and request.toolbar.edit_mode:
            found = True
        for placeholder in getattr(request, 'placeholders', []):
            if not placeholder.cache_placeholder:
                found = True
                break
        if found:
            add_never_cache_headers(response)
        if hasattr(request, 'user') and request.user.is_staff and response.status_code != 500:
            try:
                pk = LogEntry.objects.filter(
                    user=request.user,
                    action_flag__in=(ADDITION, CHANGE)
                ).only('pk').order_by('-pk')[0].pk
                if hasattr(request, 'cms_latest_entry') and request.cms_latest_entry != pk:
                    log = LogEntry.objects.filter(user=request.user, action_flag__in=(ADDITION, CHANGE))[0]
                    request.session['cms_log_latest'] = log.pk
            # If there were no LogEntries, just don't touch the session.
            # Note that in the case of a user logging-in as another user,
            # request may have a cms_latest_entry attribute, but there are no
            # LogEntries for request.user.
            except IndexError:
                pass
        return response
