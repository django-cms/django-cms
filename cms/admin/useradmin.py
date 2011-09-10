# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext as _

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from cms.admin.forms import PageUserForm, PageUserGroupForm
from cms.admin.permissionadmin import GenericCmsPermissionAdmin
from cms.exceptions import NoPermissionsException
from cms.models import PageUser, PageUserGroup
from cms.utils.permissions import get_subordinate_users


class PageUserAdmin(UserAdmin, GenericCmsPermissionAdmin):
    form = PageUserForm
    add_form = PageUserForm
    model = PageUser
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'created_by')
    
    # get_fieldsets method may add fieldsets depending on user
    fieldsets = [
        (None, {'fields': ('username', ('password1', 'password2'), 'notify_user')}),
        (_('User details'), {'fields': (('first_name', 'last_name'), 'email')}),
        (_('Groups'), {'fields': ('groups',)}),
    ]
    
    add_fieldsets = fieldsets
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = self.update_permission_fieldsets(request, obj)
        
        if not '/add' in request.path:
            fieldsets[0] = (None, {'fields': ('username', 'notify_user')})
            fieldsets.append((_('Password'), {'fields': ('password1', 'password2'), 'classes': ('collapse',)}))
        return fieldsets
    
    def queryset(self, request):
        qs = super(PageUserAdmin, self).queryset(request)
        try:
            user_id_set = get_subordinate_users(request.user).values_list('id', flat=True)
            return qs.filter(pk__in=user_id_set)
        except NoPermissionsException:
            return self.model.objects.get_empty_query_set()
    
    def add_view(self, request):
        return super(UserAdmin, self).add_view(request) 
    
class PageUserGroupAdmin(admin.ModelAdmin, GenericCmsPermissionAdmin):
    form = PageUserGroupForm
    list_display = ('name', 'created_by')
    
    fieldsets = [
        (None, {'fields': ('name',)}),
    ]
    
    def get_fieldsets(self, request, obj=None):
        return self.update_permission_fieldsets(request, obj)

if settings.CMS_PERMISSION:    
    admin.site.register(PageUser, PageUserAdmin)
    admin.site.register(PageUserGroup, PageUserGroupAdmin)