# -*- coding: utf-8 -*-
from functools import update_wrapper
import json

from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import csrf_protect_m
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import override

from cms.models import UserSettings
from cms.utils.urlutils import admin_reverse


class SettingsAdmin(ModelAdmin):
    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            url(r'^session_store/$',
                self.session_store,
                name='%s_%s_session_store' % info),
            url(r'^$',
                wrap(self.change_view),
                name='%s_%s_change' % info),
            url(r'^(.+)/$',
                wrap(self.change_view),
                name='%s_%s_change' % info),
        ]

    @csrf_protect_m
    @transaction.atomic
    def change_view(self, request, id=None):
        model = self.model
        try:
            obj = model.objects.get(user=request.user)
        except model.DoesNotExist:
            return self.add_view(request)
        return super(SettingsAdmin, self).change_view(request, str(obj.pk))

    def session_store(self, request):
        """
        either POST or GET
        POST should have a settings parameter
        """
        if not request.user.is_staff:
            return HttpResponse(json.dumps(""),
                                content_type="application/json")
        if request.method == "POST":
            request.session['cms_settings'] = request.POST['settings']
            request.session.save()
        return HttpResponse(
            json.dumps(request.session.get('cms_settings', '')),
            content_type="application/json"
        )

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
        return HttpResponseRedirect("{0}?reload_window".format(post_url))

    def has_change_permission(self, request, obj=None):
        if obj and obj.user == request.user:
            return True
        return False

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


admin.site.register(UserSettings, SettingsAdmin)
