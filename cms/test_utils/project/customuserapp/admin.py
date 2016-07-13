# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.contrib.auth.models import User as OriginalUser


if getattr(OriginalUser._meta, 'swapped', False):
    class UserAdmin(OriginalUserAdmin):
        list_display = ('username', 'email', 'get_full_name', 'is_staff')
        search_fields = ('username', 'email',)
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            ('Personal info', {'fields': ('email',)}),
            ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                        'groups', 'user_permissions')}),
            ('Important dates', {'fields': ('last_login',)}),
        )

    admin.site.register(get_user_model(), UserAdmin)
