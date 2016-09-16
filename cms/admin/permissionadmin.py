# -*- coding: utf-8 -*-
from copy import deepcopy

from django.contrib import admin
from django.contrib.admin import site
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.sites.models import Site
from django.db import OperationalError
from django.utils.translation import gettext_lazy as _

from cms.admin.forms import GlobalPagePermissionAdminForm, PagePermissionInlineAdminForm, ViewRestrictionInlineAdminForm
from cms.exceptions import NoPermissionsException
from cms.models import PagePermission, GlobalPagePermission
from cms.utils import permissions
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import classproperty


PERMISSION_ADMIN_INLINES = []

user_model = get_user_model()
admin_class = UserAdmin
for model, admin_instance in site._registry.items():
    if model == user_model:
        admin_class = admin_instance.__class__


class TabularInline(admin.TabularInline):
    pass


class PagePermissionInlineAdmin(TabularInline):
    model = PagePermission
    # use special form, so we can override of user and group field
    form = PagePermissionInlineAdminForm
    classes = ['collapse', 'collapsed']
    extra = 0  # edit page load time boost
    show_with_view_permissions = False

    @classproperty
    def raw_id_fields(cls):
        # Dynamically set raw_id_fields based on settings
        threshold = get_cms_setting('RAW_ID_USERS')

        # Given a fresh django-cms install and a django settings with the
        # CMS_RAW_ID_USERS = CMS_PERMISSION = True
        # django throws an OperationalError when running
        # ./manage migrate
        # because auth_user doesn't exists yet
        try:
            threshold = threshold and get_user_model().objects.count() > threshold
        except OperationalError:
            threshold = False

        return ['user'] if threshold else []

    def get_queryset(self, request):
        """
        Queryset change, so user with global change permissions can see
        all permissions. Otherwise user can see only permissions for
        peoples which are under him (he can't see his permissions, because
        this will lead to violation, when he can add more power to himself)
        """
        site = Site.objects.get_current(request)

        try:
            # can see only permissions for users which are under him in tree
            qs = self.model.objects.subordinate_to_user(request.user, site)
        except NoPermissionsException:
            return self.model.objects.none()
        return qs.filter(can_view=self.show_with_view_permissions)

    def get_formset(self, request, obj=None, **kwargs):
        """
        Some fields may be excluded here. User can change only
        permissions which are available for him. E.g. if user does not haves
        can_publish flag, he can't change assign can_publish permissions.
        """
        exclude = self.exclude or []
        if obj:
            user = request.user
            if not obj.has_add_permission(user):
                exclude.append('can_add')
            if not obj.has_delete_permission(user):
                exclude.append('can_delete')
            if not obj.has_publish_permission(user):
                exclude.append('can_publish')
            if not obj.has_advanced_settings_permission(user):
                exclude.append('can_change_advanced_settings')
            if not obj.has_move_page_permission(user):
                exclude.append('can_move_page')

        kwargs['exclude'] = exclude
        formset_cls = super(PagePermissionInlineAdmin, self).get_formset(request, obj=obj, **kwargs)
        qs = self.get_queryset(request)
        if obj is not None:
            qs = qs.filter(page=obj)
        formset_cls._queryset = qs
        return formset_cls


class ViewRestrictionInlineAdmin(PagePermissionInlineAdmin):
    extra = 0  # edit page load time boost
    form = ViewRestrictionInlineAdminForm
    verbose_name = _("View restriction")
    verbose_name_plural = _("View restrictions")
    show_with_view_permissions = True


class GlobalPagePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
    list_filter = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']

    form = GlobalPagePermissionAdminForm
    search_fields = []
    for field in admin_class.search_fields:
        search_fields.append("user__%s" % field)
    search_fields.append('group__name')

    list_display.append('can_change_advanced_settings')
    list_filter.append('can_change_advanced_settings')

    def get_list_filter(self, request):
        threshold = get_cms_setting('RAW_ID_USERS')
        try:
            threshold = threshold and get_user_model().objects.count() > threshold
        except OperationalError:
            threshold = False
        filter_copy = deepcopy(self.list_filter)
        if threshold:
            filter_copy.remove('user')
        return filter_copy

    def has_add_permission(self, request):
        site = Site.objects.get_current(request)
        return permissions.user_can_add_global_permissions(request.user, site)

    def has_change_permission(self, request, obj=None):
        site = Site.objects.get_current(request)
        return permissions.user_can_change_global_permissions(request.user, site)

    def has_delete_permission(self, request, obj=None):
        site = Site.objects.get_current(request)
        return permissions.user_can_delete_global_permissions(request.user, site)

    @classproperty
    def raw_id_fields(cls):
        # Dynamically set raw_id_fields based on settings
        threshold = get_cms_setting('RAW_ID_USERS')

        # Given a fresh django-cms install and a django settings with the
        # CMS_RAW_ID_USERS = CMS_PERMISSION = True
        # django throws an OperationalError when running
        # ./manage migrate
        # because auth_user doesn't exists yet
        try:
            threshold = threshold and get_user_model().objects.count() > threshold
        except OperationalError:
            threshold = False

        return ['user'] if threshold else []


if get_cms_setting('PERMISSION'):
    admin.site.register(GlobalPagePermission, GlobalPagePermissionAdmin)
    PERMISSION_ADMIN_INLINES.extend([
        ViewRestrictionInlineAdmin,
        PagePermissionInlineAdmin,
    ])
