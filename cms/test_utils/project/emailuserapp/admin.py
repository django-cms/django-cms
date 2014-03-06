# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin

from .models import EmailUser
from .forms import UserChangeForm, UserCreationForm


class UserAdmin(OriginalUserAdmin):
    # The form to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # Overrides the field lists from UserAdmin
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # UserAdmin overrides get_fieldsets to use this attribute
    # so it must be populated
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )

    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('last_name', 'first_name', 'email')

# Now register the emailuser admin

admin.site.register(EmailUser, UserAdmin)
