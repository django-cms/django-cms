# -*- coding: utf-8 -*-
from cms.admin.forms import (GlobalPagePermissionAdminForm, 
    PagePermissionInlineAdminForm, ViewRestrictionInlineAdminForm)
from cms.exceptions import NoPermissionsException
from cms.models import Page, PagePermission, GlobalPagePermission, PageUser
from cms.utils.permissions import get_user_permission_level
from copy import deepcopy
from distutils.version import LooseVersion
from django.conf import settings
from django.contrib import admin
from django.template.defaultfilters import title
from django.utils.translation import ugettext as _
import django



DJANGO_1_3 = LooseVersion(django.get_version()) < LooseVersion('1.4')
PAGE_ADMIN_INLINES = []


class TabularInline(admin.TabularInline):
    pass

if DJANGO_1_3 and 'reversion' in settings.INSTALLED_APPS:
    """
    Backwards compatibility for Django < 1.4 and django-reversion 1.6
    """
    class TabularInline(TabularInline):
        def get_prepopulated_fields(self, request, obj=None):
            return self.prepopulated_fields
    from reversion.admin import helpers
    class CompatInlineAdminFormSet(helpers.InlineAdminFormSet):
        def __init__(self, inline, formset, fieldsets, prepopulated_fields=None,
                readonly_fields=None, model_admin=None):
            super(CompatInlineAdminFormSet, self).__init__(inline, formset, fieldsets, readonly_fields, model_admin)
    helpers.InlineAdminFormSet = CompatInlineAdminFormSet


class PagePermissionInlineAdmin(TabularInline):
    model = PagePermission
    # use special form, so we can override of user and group field
    form = PagePermissionInlineAdminForm
    classes = ['collapse', 'collapsed']
    exclude = ['can_view']
    extra = 0 # edit page load time boost
    
    def queryset(self, request):
        """
        Queryset change, so user with global change permissions can see
        all permissions. Otherwise can user see only permissions for 
        peoples which are under him (he can't see his permissions, because
        this will lead to violation, when he can add more power to itself)
        """
        # can see only permissions for users which are under him in tree

        ### here a exception can be thrown
        try:
            qs = PagePermission.objects.subordinate_to_user(request.user)
            return qs.filter(can_view=False)
        except NoPermissionsException:
            return self.objects.get_empty_query_set()
    
    def get_formset(self, request, obj=None, **kwargs):
        """
        Some fields may be excluded here. User can change only
        permissions which are available for him. E.g. if user does not haves
        can_publish flag, he can't change assign can_publish permissions.
        """
        exclude = self.exclude or []
        if obj:
            if not obj.has_add_permission(request):
                exclude.append('can_add')
            if not obj.has_delete_permission(request):
                exclude.append('can_delete')
            if not obj.has_publish_permission(request):
                exclude.append('can_publish')
            if not obj.has_advanced_settings_permission(request):
                exclude.append('can_change_advanced_settings')
            if not obj.has_move_page_permission(request):
                exclude.append('can_move_page')
            if not settings.CMS_MODERATOR or not obj.has_moderate_permission(request):
                exclude.append('can_moderate')
        formset_cls = super(PagePermissionInlineAdmin, self
            ).get_formset(request, obj=None, exclude=exclude, *kwargs)
        qs = self.queryset(request)
        if obj is not None:
            qs = qs.filter(page=obj)
        formset_cls._queryset = qs
        return formset_cls

class ViewRestrictionInlineAdmin(PagePermissionInlineAdmin):
    extra = 0 # edit page load time boost
    form = ViewRestrictionInlineAdminForm
    verbose_name = _("View restriction")
    verbose_name_plural = _("View restrictions")
    exclude = [
        'can_add', 'can_change', 'can_delete', 'can_view',
        'can_publish', 'can_change_advanced_settings', 'can_move_page',
        'can_moderate', 'can_change_permissions'
    ]

    def get_formset(self, request, obj=None, **kwargs):
        """
        Some fields may be excluded here. User can change only permissions
        which are available for him. E.g. if user does not haves can_publish
        flag, he can't change assign can_publish permissions.
        """
        formset_cls = super(PagePermissionInlineAdmin, self).get_formset(request, obj, **kwargs)
        qs = self.queryset(request)
        if obj is not None:
            qs = qs.filter(page=obj)
        formset_cls._queryset = qs
        return formset_cls

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = PagePermission.objects.subordinate_to_user(request.user)
        return qs.filter(can_view=True)


class GlobalPagePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
    list_filter = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
    
    form = GlobalPagePermissionAdminForm
    
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'group__name')
    
    exclude = []
    
    list_display.append('can_change_advanced_settings')
    list_filter.append('can_change_advanced_settings')
    
    if settings.CMS_MODERATOR:
        list_display.append('can_moderate')
        list_filter.append('can_moderate')
    else:
        exclude.append('can_moderate')


class GenericCmsPermissionAdmin(object):
    """
    Custom mixin for permission-enabled admin interfaces.
    """
    def update_permission_fieldsets(self, request, obj=None):
        """
        Nobody can grant more than he haves, so check for user permissions
        to Page and User model and render fieldset depending on them.
        """
        fieldsets = deepcopy(self.fieldsets)
        perm_models = (
            (Page, _('Page permissions')),
            (PageUser, _('User & Group permissions')),
            (PagePermission, _('Page permissions management')),
        )
        for i, perm_model in enumerate(perm_models):
            model, title = perm_model
            opts, fields = model._meta, []
            name = model.__name__.lower()
            for t in ('add', 'change', 'delete'):
                fn = getattr(opts, 'get_%s_permission' % t)
                if request.user.has_perm(opts.app_label + '.' + fn()):
                    fields.append('can_%s_%s' % (t, name))
            if fields:
                fieldsets.insert(2 + i, (title, {'fields': (fields,)}))
        return fieldsets
    
    def _has_change_permissions_permission(self, request):
        """
        User is able to add/change objects only if he haves can change
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


if settings.CMS_PERMISSION:
    admin.site.register(GlobalPagePermission, GlobalPagePermissionAdmin)
    PAGE_ADMIN_INLINES.extend([
        ViewRestrictionInlineAdmin,
        PagePermissionInlineAdmin,
    ])
