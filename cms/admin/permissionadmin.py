# -*- coding: utf-8 -*-
from copy import deepcopy
from django.contrib import admin
from django.contrib.admin import site
from django.contrib.auth import get_user_model, get_permission_codename
from django.contrib.auth.admin import UserAdmin
from django.db import OperationalError
from django.utils.translation import ugettext, ugettext_lazy as _

from cms.admin.forms import GlobalPagePermissionAdminForm, PagePermissionInlineAdminForm, ViewRestrictionInlineAdminForm
from cms.exceptions import NoPermissionsException
from cms.models import Page, PagePermission, GlobalPagePermission, PageUser
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import classproperty
from cms.utils.permissions import get_user_permission_level

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
    exclude = ['can_view']
    extra = 0  # edit page load time boost

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
        all permissions. Otherwise can user see only permissions for
        peoples which are under him (he can't see his permissions, because
        this will lead to violation, when he can add more power to itself)
        """
        # can see only permissions for users which are under him in tree

        # here an exception can be thrown
        try:
            qs = self.model.objects.subordinate_to_user(request.user)
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
        formset_cls = super(PagePermissionInlineAdmin, self
        ).get_formset(request, obj=None, exclude=exclude, **kwargs)
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
    exclude = [
        'can_add', 'can_change', 'can_delete', 'can_view',
        'can_publish', 'can_change_advanced_settings', 'can_move_page',
        'can_change_permissions'
    ]

    def get_formset(self, request, obj=None, **kwargs):
        """
        Some fields may be excluded here. User can change only permissions
        which are available for him. E.g. if user does not haves can_publish
        flag, he can't change assign can_publish permissions.
        """
        formset_cls = super(PagePermissionInlineAdmin, self).get_formset(request, obj, **kwargs)
        qs = self.get_queryset(request)
        if obj is not None:
            qs = qs.filter(page=obj)
        formset_cls._queryset = qs
        return formset_cls

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model.objects.subordinate_to_user(request.user)
        return qs.filter(can_view=True)


class GlobalPagePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
    list_filter = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']

    form = GlobalPagePermissionAdminForm
    search_fields = []
    for field in admin_class.search_fields:
        search_fields.append("user__%s" % field)
    search_fields.append('group__name')

    exclude = []

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
            (Page, ugettext('Page permissions')),
            (PageUser, ugettext('User & Group permissions')),
            (PagePermission, ugettext('Page permissions management')),
        )
        for i, perm_model in enumerate(perm_models):
            model, title = perm_model
            opts, fields = model._meta, []
            name = model.__name__.lower()
            for key in ('add', 'change', 'delete'):
                perm_code = '%s.%s' % (opts.app_label, get_permission_codename(key, opts))
                if request.user.has_perm(perm_code):
                    fields.append('can_%s_%s' % (key, name))
            if fields:
                fieldsets.insert(2 + i, (title, {'fields': (fields,)}))
        return fieldsets

    def _has_change_permissions_permission(self, request):
        """
        User is able to add/change objects only if he haves can change
        permission on some page.
        """
        try:
            get_user_permission_level(request.user)
        except NoPermissionsException:
            return False
        return True

    def has_add_permission(self, request):
        return self._has_change_permissions_permission(request) and \
               super(self.__class__, self).has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_change_permissions_permission(request) and \
               super(self.__class__, self).has_change_permission(request, obj)


if get_cms_setting('PERMISSION'):
    admin.site.register(GlobalPagePermission, GlobalPagePermissionAdmin)
    PERMISSION_ADMIN_INLINES.extend([
        ViewRestrictionInlineAdmin,
        PagePermissionInlineAdmin,
    ])
