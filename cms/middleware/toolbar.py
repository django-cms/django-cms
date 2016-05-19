# -*- coding: utf-8 -*-
"""
Edit Toolbar middleware
"""
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.core.urlresolvers import resolve
from django.http import HttpResponse

from cms.toolbar.toolbar import CMSToolbar
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import force_language
from cms.utils.request_ip_resolvers import get_request_ip_resolver
from menus.menu_pool import menu_pool

get_request_ip = get_request_ip_resolver()


def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    toolbar = original_context['request'].toolbar

    instance.placeholder = placeholder

    with force_language(toolbar.toolbar_language):
        data = {
            'instance': instance,
            'rendered_content': rendered_content,
        }
        # TODO: Remove js_compat once get_action_urls is refactored.
        data.update(instance.get_action_urls(js_compat=False))

    original_context.update(data)
    template = toolbar.get_cached_template(
        template=instance.get_plugin_class().frontend_edit_template
    )
    output = template.render(original_context).strip()
    original_context.pop()
    return output


class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def is_cms_request(self, request):
        toolbar_hide = get_cms_setting('TOOLBAR_HIDE')
        internal_ips = get_cms_setting('INTERNAL_IPS')

        if internal_ips:
            client_ip = get_request_ip(request)
            if client_ip not in internal_ips:
                return False

        if not toolbar_hide:
            return True

        try:
            match = resolve(request.path_info)
        except:
            return False

        return match.url_name in ('pages-root', 'pages-details-by-slug')

    def process_request(self, request):
        """
        If we should show the toolbar for this request, put it on
        request.toolbar. Then call the request_hook on the toolbar.
        """

        if not self.is_cms_request(request):
            return

        edit_on = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        edit_off = get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        build = get_cms_setting('CMS_TOOLBAR_URL__BUILD')
        disable = get_cms_setting('CMS_TOOLBAR_URL__DISABLE')
        anonymous_on = get_cms_setting('TOOLBAR_ANONYMOUS_ON')

        if disable in request.GET:
            request.session['cms_toolbar_disabled'] = True
        if edit_on in request.GET:  # If we actively enter edit mode, we should show the toolbar in any case
            request.session['cms_toolbar_disabled'] = False

        if not request.session.get('cms_toolbar_disabled', False) and (
                request.user.is_staff or (anonymous_on and request.user.is_anonymous())
        ):
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
        if not self.is_cms_request(request):
            return

        response = request.toolbar.request_hook()
        if isinstance(response, HttpResponse):
            return response

    def process_response(self, request, response):
        if not self.is_cms_request(request):
            return response

        from django.utils.cache import add_never_cache_headers

        if ((hasattr(request, 'toolbar') and request.toolbar.edit_mode) or
                not all(ph.cache_placeholder
                        for ph, __ in getattr(request, 'placeholders', {}).values())):
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
