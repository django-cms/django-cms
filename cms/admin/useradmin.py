# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.contrib import admin

from cms.admin.forms import PageUserForm, PageUserGroupForm
from cms.admin.permissionadmin import GenericCmsPermissionAdmin
from cms.exceptions import NoPermissionsException
from cms.models import PageUser, PageUserGroup
from cms.utils.compat.dj import get_user_model
from cms.utils.compat.forms import UserAdmin
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import get_subordinate_users

class PageUserAdmin(UserAdmin, GenericCmsPermissionAdmin):
    form = PageUserForm
    add_form = PageUserForm
    model = PageUser
    
    list_display = ('email', 'first_name', 'last_name', 'created_by')

    if get_user_model().USERNAME_FIELD != 'email':
        list_display += (get_user_model().USERNAME_FIELD,)
    
    # get_fieldsets method may add fieldsets depending on user
    fieldsets = [
        (None, {'fields': (get_user_model().USERNAME_FIELD, ('password1', 'password2'), 'notify_user')}),
    ]

    if get_user_model().USERNAME_FIELD != 'email':
        fieldsets.append((_('User details'), {'fields': (('first_name', 'last_name'), 'email')}))
    else:
        fieldsets.append((_('User details'), {'fields': (('first_name', 'last_name'))}))
        
    fieldsets.append((_('Groups'), {'fields': ('groups',)}))
    
    add_fieldsets = fieldsets

    ordering = ('last_name', 'first_name', 'email')

    if get_user_model().USERNAME_FIELD != 'email':
        ordering = (get_user_model().USERNAME_FIELD,) + ordering
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = self.update_permission_fieldsets(request, obj)
        
        if not '/add' in request.path:
            fieldsets[0] = (None, {'fields': (get_user_model().USERNAME_FIELD, 'notify_user')})
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

if get_cms_setting('PERMISSION'):
    admin.site.register(PageUser, PageUserAdmin)
    admin.site.register(PageUserGroup, PageUserGroupAdmin)
