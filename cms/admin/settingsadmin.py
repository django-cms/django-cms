# -*- coding: utf-8 -*-
from functools import update_wrapper
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import csrf_protect_m
from django.contrib.admin import ModelAdmin

from django.contrib import admin

from cms.models import UserSettings
from django.core.urlresolvers import reverse
from django.db import transaction


class SettingsAdmin(ModelAdmin):
    def get_urls(self):
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns(
            '',
            url(r'^$',
                wrap(self.change_view),
                name='%s_%s_change' % info),
        )
        return urlpatterns

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request):
        model = self.model
        try:
            obj = model.objects.get(user=request.user)
        except model.DoesNotExist:
            return self.add_view(request)
        return super(SettingsAdmin, self).change_view(request, str(obj.pk))

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def response_post_save_change(self, request, obj):
        post_url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url)

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
