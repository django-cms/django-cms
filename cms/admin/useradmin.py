from copy import deepcopy

from django.contrib import admin
from django.contrib.admin import site
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.translation import gettext

from cms.admin.forms import PageUserChangeForm, PageUserGroupForm
from cms.exceptions import NoPermissionsException
from cms.models import Page, PagePermission, PageUser, PageUserGroup
from cms.utils.compat.forms import UserAdmin
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import (
    get_model_permission_codename, get_subordinate_groups,
    get_subordinate_users, get_user_permission_level,
)

user_model = get_user_model()
admin_class = UserAdmin
for model, admin_instance in site._registry.items():
    if model == user_model:
        admin_class = admin_instance.__class__


class GenericCmsPermissionAdmin:

    def get_subordinates(self, user, site):
        raise NotImplementedError

    def _has_change_permissions_permission(self, request):
        """
        User is able to add/change objects only if he haves can change
        permission on some page.
        """
        site = Site.objects.get_current(request)

        try:
            get_user_permission_level(request.user, site)
        except NoPermissionsException:
            return False
        return True

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        form_class._current_user = request.user
        return form_class

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        site = Site.objects.get_current(request)
        user_ids = self.get_subordinates(request.user, site).values_list('pk', flat=True)
        return queryset.filter(pk__in=user_ids)

    def has_add_permission(self, request):
        has_model_perm = super().has_add_permission(request)

        if not has_model_perm:
            return False
        return self._has_change_permissions_permission(request)

    def has_change_permission(self, request, obj=None):
        has_model_perm = super().has_change_permission(request, obj)

        if not has_model_perm:
            return False
        return self._has_change_permissions_permission(request)

    def has_delete_permission(self, request, obj=None):
        has_model_perm = super().has_delete_permission(request, obj)

        if not has_model_perm:
            return False
        return self._has_change_permissions_permission(request)

    def has_view_permission(self, request, obj=None):
        # For django 2.1
        # Default is to return True if user got `change` perm, but we have to
        # get in consideration also cms permission system
        return self.has_change_permission(request, obj)


class PageUserAdmin(GenericCmsPermissionAdmin, admin_class):
    form = PageUserChangeForm
    model = PageUser

    def get_subordinates(self, user, site):
        return get_subordinate_users(user, site).values_list('pk', flat=True)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)

        if not request.user.is_superuser:
            # Non superusers can't set superuser status on
            # their subordinates.
            fields = list(fields) + ['is_superuser']
        return fields

    def save_model(self, request, obj, form, change):
        if not change:
            # By default set the staff flag to True
            # when a PageUser is first created
            obj.is_staff = True
            # Set the created_by field to the current user
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PageUserGroupAdmin(GenericCmsPermissionAdmin, admin.ModelAdmin):
    form = PageUserGroupForm
    list_display = ('name', 'created_by')

    fieldsets = [
        (None, {'fields': ('name',)}),
    ]

    def get_fieldsets(self, request, obj=None):
        """
        Nobody can grant more than he haves, so check for user permissions
        to Page and User model and render fieldset depending on them.
        """
        fieldsets = deepcopy(self.fieldsets)
        perm_models = (
            (Page, gettext('Page permissions')),
            (PageUser, gettext('User & Group permissions')),
            (PagePermission, gettext('Page permissions management')),
        )
        for i, perm_model in enumerate(perm_models):
            fields = []
            model, title = perm_model
            name = model.__name__.lower()
            for key in ('add', 'change', 'delete'):
                perm_code = get_model_permission_codename(model, action=key)
                if request.user.has_perm(perm_code):
                    fields.append('can_%s_%s' % (key, name))
            if fields:
                fieldsets.insert(2 + i, (title, {'fields': (fields,)}))
        return fieldsets

    def get_subordinates(self, user, site):
        return get_subordinate_groups(user, site).values_list('pk', flat=True)


if get_cms_setting('PERMISSION'):
    admin.site.register(PageUser, PageUserAdmin)
    admin.site.register(PageUserGroup, PageUserGroupAdmin)
