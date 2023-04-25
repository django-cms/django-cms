"""
Edit Toolbar middleware
"""
from django import forms
from django.core.exceptions import ValidationError
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.request_ip_resolvers import get_request_ip_resolver

get_request_ip = get_request_ip_resolver()


class ToolbarMiddleware(MiddlewareMixin):
    """
    Middleware to set up CMS Toolbar.
    """

    def is_edit_mode(self, request):
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return False

        return match.url_name == 'cms_placeholder_render_object_edit'

    def is_cms_request(self, request):
        toolbar_hide = get_cms_setting('TOOLBAR_HIDE')
        internal_ips = get_cms_setting('INTERNAL_IPS')

        if internal_ips:
            client_ip = get_request_ip(request)
            try:
                client_ip = forms.GenericIPAddressField().clean(client_ip)
            except ValidationError:
                return False
            else:
                if client_ip not in internal_ips:
                    return False

        if not toolbar_hide:
            return True

        try:
            match = resolve(request.path_info)
        except Resolver404:
            return False

        return match.url_name in ('pages-root', 'pages-details-by-slug')

    def process_request(self, request):
        """
        If we should show the toolbar for this request, put it on
        request.toolbar. Then call the request_hook on the toolbar.
        """

        if not self.is_cms_request(request):
            return

        persist = get_cms_setting('CMS_TOOLBAR_URL__PERSIST')
        enable_toolbar = get_cms_setting('CMS_TOOLBAR_URL__ENABLE')
        disable_toolbar = get_cms_setting('CMS_TOOLBAR_URL__DISABLE')
        field = forms.BooleanField(required=False)

        if field.clean(request.GET.get(persist, True)):
            if disable_toolbar in request.GET:
                request.session['cms_toolbar_disabled'] = True

            if enable_toolbar in request.GET or self.is_edit_mode(request):
                request.session['cms_toolbar_disabled'] = False

        request.toolbar = SimpleLazyObject(lambda: CMSToolbar(request))

    def process_response(self, request, response):
        if not self.is_cms_request(request):
            return response

        from django.utils.cache import add_never_cache_headers

        toolbar = get_toolbar_from_request(request)

        if toolbar._cache_disabled:
            add_never_cache_headers(response)
        return response
