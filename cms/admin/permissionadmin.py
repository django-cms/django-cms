from django.conf import settings
from cms.admin.forms import GlobalPagePermissionAdminForm, \
    PagePermissionInlineAdminForm
from cms.admin.models import BaseInlineFormSetWithQuerySet
from cms.exceptions import NoPermissionsException
from cms.models import Page, PagePermission, GlobalPagePermission, PageUser
from cms.utils.permissions import get_user_permission_level
from copy import deepcopy
from django.contrib import admin
from django.template.defaultfilters import title
from django.utils.translation import ugettext as _

PAGE_ADMIN_INLINES = []

################################################################################
# Permissions
################################################################################

class PagePermissionInlineAdmin(admin.TabularInline):
    model = PagePermission
    # use special form, so we can override of user and group field
    form = PagePermissionInlineAdminForm
    # use special formset, so we can use queryset defined here
    formset = BaseInlineFormSetWithQuerySet
    classes = ['collapse', 'collapsed'] 
    
    def __init__(self, *args, **kwargs):
        super(PagePermissionInlineAdmin, self).__init__(*args, **kwargs)
    
    def queryset(self, request):
        """Queryset change, so user with global change permissions can see
        all permissions. Otherwise can user see only permissions for 
        peoples which are under him (he can't see his permissions, because
        this will lead to violation, when he can add more power to itself)
        """
        # can see only permissions for users which are under him in tree
        qs = PagePermission.objects.subordinate_to_user(request.user)
        return qs
    
    def get_fieldsets(self, request, obj=None):
        """Request formset with given obj.
        """
        if self.declared_fieldsets:
            return self.declared_fieldsets
        form = self.get_formset(request, obj).form
        return [(None, {'fields': form.base_fields.keys()})]
    
    def get_formset(self, request, obj=None, **kwargs):
        """Some fields may be excluded here. User can change only 
        permissions which are available for him. E.g. if user does not haves 
        can_publish flag, he can't change assign can_publish permissions.
        
        Seems django doesn't cares about queryset defined here - its
        probably a bug, so monkey patching again.. Assign use_queryset
        attribute to FormSet, our overiden formset knows how to handle this, 
        @see BaseInlineFormSetWithQuerySet for more details.
        """
        if obj:
            self.exclude = []
            if not obj.has_add_permission(request):
                self.exclude.append('can_add')
            if not obj.has_delete_permission(request):
                self.exclude.append('can_delete')
            if not obj.has_publish_permission(request):
                self.exclude.append('can_publish')
            if not obj.has_advanced_settings_permission(request):
                self.exclude.append('can_change_advanced_settings')
            if not obj.has_move_page_permission(request):
                self.exclude.append('can_move_page')
            if not settings.CMS_MODERATOR or not obj.has_moderate_permission(request):
                self.exclude.append('can_moderate')
        FormSet = super(PagePermissionInlineAdmin, self).get_formset(request, obj=None, **kwargs)
        # asign queryset 
        FormSet.use_queryset = self.queryset(request)
        return FormSet

if settings.CMS_PERMISSION: 
    PAGE_ADMIN_INLINES.append(PagePermissionInlineAdmin)


class GlobalPagePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
    list_filter = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
    
    form = GlobalPagePermissionAdminForm
    
    search_fields = ('user__username', 'user__firstname', 'user__lastname', 'group__name')
    
    exclude = []
    
    list_display.append('can_change_advanced_settings')
    list_filter.append('can_change_advanced_settings')
        
    if settings.CMS_MODERATOR:
        list_display.append('can_moderate')
        list_filter.append('can_moderate')
    else:
        exclude.append('can_moderate')

if settings.CMS_PERMISSION:    
    admin.site.register(GlobalPagePermission, GlobalPagePermissionAdmin)


class GenericCmsPermissionAdmin(object):
    def update_permission_fieldsets(self, request, obj=None):
        """Nobody can grant more than he haves, so check for user 
        permissions to Page and User model and render fieldset depending on
        them.
        """
        fieldsets = deepcopy(self.fieldsets)
        
        models = (
            (Page, _('Page permissions')),
            (PageUser, _('User & Group permissions')),
            (PagePermission, _('Page permissions management')),
        )
        
        i = 0
        for model, title in models:
            opts, fields = model._meta, []
            name = model.__name__.lower()
            for t in ('add', 'change', 'delete'):
                fn = getattr(opts, 'get_%s_permission' % t)
                if request.user.has_perm(opts.app_label + '.' + fn()):
                    fields.append('can_%s_%s' % (t, name))
            if fields:
                fieldsets.insert(2 + i, (title, {'fields': (fields,)}))
            i += 1
        return fieldsets
            
    def _has_change_permissions_permission(self, request):
        """User is able to add/change objects only if he haves can change
        permission on some page.
        """
        try:
            user_level = get_user_permission_level(request.user)
        except NoPermissionsException:
            return False
        return True
    
    def has_add_permission(self, request):
        return self._has_change_permissions_permission(request) and \
            super(self.__class__, self).has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_change_permissions_permission(request) and \
            super(self.__class__, self).has_change_permission(request, obj)

