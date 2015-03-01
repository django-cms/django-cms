# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth import get_user_model

from cms.admin.forms import PageUserForm, PageUserGroupForm
from cms.admin.permissionadmin import GenericCmsPermissionAdmin
from cms.exceptions import NoPermissionsException
from cms.models import PageUser, PageUserGroup
from cms.utils.compat.forms import UserAdmin
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import get_subordinate_users
from django.contrib.admin import site

user_model = get_user_model()
admin_class = UserAdmin
for model, admin_instance in site._registry.items():
    if model == user_model:
        admin_class = admin_instance.__class__

class PageUserAdmin(admin_class, GenericCmsPermissionAdmin):
    form = PageUserForm
    add_form = PageUserForm
    model = PageUser

    def get_queryset(self, request):
        qs = super(PageUserAdmin, self).get_queryset(request)
        try:
            user_id_set = get_subordinate_users(request.user).values_list('id', flat=True)
            return qs.filter(pk__in=user_id_set)
        except NoPermissionsException:
            return self.model.objects.get_empty_query_set()


class PageUserGroupAdmin(admin.ModelAdmin, GenericCmsPermissionAdmin):
    form = PageUserGroupForm
    list_display = ('name', 'created_by')

    fieldsets = [
        (None, {'fields': ('name',)}),
    ]

    def get_fieldsets(self, request, obj=None):
        return self.update_permission_fieldsets(request, obj)

if get_cms_setting('PERMISSION'):
    admin.site.register(PageUser, PageUserAdmin)
    admin.site.register(PageUserGroup, PageUserGroupAdmin)
