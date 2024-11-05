import copy
import json
from functools import update_wrapper
from urllib.parse import urlparse

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import csrf_protect_m
from django.db import transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.http.request import QueryDict
from django.urls import Resolver404, path, re_path, resolve
from django.utils.html import conditional_escape
from django.utils.translation import override

from cms.admin.forms import RequestToolbarForm
from cms.models import UserSettings
from cms.utils.page import get_page_from_request
from cms.utils.urlutils import admin_reverse


@admin.register(UserSettings)
class SettingsAdmin(ModelAdmin):

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('session_store/', self.session_store, name='%s_%s_session_store' % info),
            path('cms-toolbar/', wrap(self.get_toolbar), name='%s_%s_get_toolbar' % info),
            path('', wrap(self.change_view), name='%s_%s_change' % info),
            re_path(r'^(.+)/$', wrap(self.change_view), name='%s_%s_change' % info),
        ]

    @csrf_protect_m
    @transaction.atomic
    def change_view(self, request, id=None):
        model = self.model
        try:
            obj = model.objects.get(user=request.user)
        except model.DoesNotExist:
            return self.add_view(request)
        return super().change_view(request, str(obj.pk))

    def session_store(self, request):
        """
        either POST or GET
        POST should have a settings parameter
        """
        if not request.user.is_staff:
            return HttpResponse(json.dumps(""),
                                content_type="application/json")
        if request.method == "POST":
            request.session['cms_settings'] = conditional_escape(request.POST['settings'])
            request.session.save()
        return HttpResponse(
            json.dumps(request.session.get('cms_settings', '')),
            content_type="application/json"
        )

    def get_toolbar(self, request):
        from cms.toolbar.toolbar import CMSToolbar

        form = RequestToolbarForm(request.GET or None)

        if not form.is_valid():
            return HttpResponseBadRequest('Invalid parameters')

        form_data = form.cleaned_data
        cms_path = form_data.get('cms_path') or request.path_info
        origin_url = urlparse(cms_path)
        attached_obj = form_data.get('attached_obj')
        current_page = get_page_from_request(request, use_path=origin_url.path, clean_path=True)

        if attached_obj and current_page and not (attached_obj == current_page):
            return HttpResponseBadRequest('Generic object does not match current page')

        data = QueryDict(query_string=origin_url.query, mutable=True)
        placeholders = request.GET.getlist("placeholders[]")

        if placeholders:
            data.setlist('placeholders[]', placeholders)

        request = copy.copy(request)
        request.GET = data
        request.current_page = current_page
        try:
            request.resolver_match = resolve(origin_url.path)
        except Resolver404:
            pass
        request.toolbar = CMSToolbar(request, request_path=origin_url.path, _async=True)
        request.toolbar.set_object(attached_obj or current_page)
        return HttpResponse(request.toolbar.render())

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def response_post_save_change(self, request, obj):
        #
        # When the user changes his language setting, we need to do two things:
        # 1. Change the language-prefix for the sideframed admin view
        # 2. Reload the whole window so that the new language affects the
        #    toolbar, etc.
        #
        # To do this, we first redirect the sideframe to the correct new, URL,
        # but we pass a GET param 'reload_window', which instructs JS on that
        # page to strip (to avoid infinite redirection loops) that param then
        # reload the whole window again.
        #
        with override(obj.language):
            post_url = admin_reverse(
                'cms_usersettings_change',
                args=[obj.id, ],
                current_app=self.admin_site.name
            )
        return HttpResponseRedirect(f"{post_url}?reload_window")

    def has_change_permission(self, request, obj=None):
        if obj and obj.user == request.user:
            return True
        return False

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


