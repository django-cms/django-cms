# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth import get_user_model

from cms.admin.forms import PageUserForm, PageUserGroupForm
from cms.admin.permissionadmin import GenericCmsPermissionAdmin
from cms.exceptions import NoPermissionsException
from cms.models import PageUser, PageUserGroup
from cms.utils.compat.forms import UserAdmin
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import get_subordinate_groups, get_subordinate_users
from django.contrib.admin import site

user_model = get_user_model()
admin_class = UserAdmin
for model, admin_instance in site._registry.items():
    if model == user_model:
        admin_class = admin_instance.__class__


class PageUserAdmin(GenericCmsPermissionAdmin, admin_class):
    form = PageUserForm
    add_form = PageUserForm
    model = PageUser

    def get_queryset(self, request):
        queryset = super(PageUserAdmin, self).get_queryset(request)

        try:
            user_ids = get_subordinate_users(request.user).values_list('pk', flat=True)
            return queryset.filter(pk__in=user_ids)
        except NoPermissionsException:
            return self.model.objects.none()


class PageUserGroupAdmin(GenericCmsPermissionAdmin, admin.ModelAdmin):
    form = PageUserGroupForm
    list_display = ('name', 'created_by')

    fieldsets = [
        (None, {'fields': ('name',)}),
    ]

    def get_fieldsets(self, request, obj=None):
        return self.update_permission_fieldsets(request, obj)

    def get_queryset(self, request):
        queryset = super(PageUserGroupAdmin, self).get_queryset(request)

        try:
            group_ids = get_subordinate_groups(request.user).values_list('pk', flat=True)
            return queryset.filter(pk__in=group_ids)
        except NoPermissionsException:
            return self.model.objects.none()


if get_cms_setting('PERMISSION'):
    admin.site.register(PageUser, PageUserAdmin)
    admin.site.register(PageUserGroup, PageUserGroupAdmin)
