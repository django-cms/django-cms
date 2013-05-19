# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as OriginalUser
from cms.compat import User


if getattr(OriginalUser._meta, 'swapped', False):
    class CustomUserAdmin(UserAdmin):
        def get_urls(self):
            from functools import update_wrapper
            from django.conf.urls import patterns, url

            def wrap(view):
                def wrapper(*args, **kwargs):
                    return self.admin_site.admin_view(view)(*args, **kwargs)
                return update_wrapper(wrapper, view)

            urlpatterns = patterns('',
                url(r'^$',
                    wrap(self.changelist_view),
                    name='auth_user_changelist'),
                url(r'^add/$',
                    wrap(self.add_view),
                    name='auth_user_add'),
                url(r'^(.+)/history/$',
                    wrap(self.history_view),
                    name='auth_user_history'),
                url(r'^(.+)/delete/$',
                    wrap(self.delete_view),
                    name='auth_user_delete'),
                url(r'^(.+)/$',
                    wrap(self.change_view),
                    name='auth_user_change'),
            )
            urlpatterns = urlpatterns + super(CustomUserAdmin, self).get_urls()
            return urlpatterns

    admin.site.register(User, CustomUserAdmin)