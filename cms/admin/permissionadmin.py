from django.contrib import admin
from django.contrib.admin import site
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _

from cms.exceptions import NoPermissionsException
from cms.models import GlobalPagePermission, PagePermission
from cms.utils import page_permissions, permissions
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import get_subordinate_users, get_subordinate_groups

PERMISSION_ADMIN_INLINES = []

user_model = get_user_model()
admin_class = UserAdmin
for model, admin_instance in site._registry.items():
    if model == user_model:
        admin_class = admin_instance.__class__


class PagePermissionMixin:
    def has_change_permission(self, request, obj=None):
        if not obj:
            return False
        return page_permissions.user_can_change_page_permissions(
            request.user,
            page=obj,
            site=obj.node.site,
        )

    def has_add_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

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
            queryset = self.model.objects.subordinate_to_user(request.user, site)
        except NoPermissionsException:
            return self.model.objects.none()
        return queryset

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        site = Site.objects.get_current(request)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'user':
            formfield._queryset = get_subordinate_users(request.user, site)
        if db_field.name == 'group':
            formfield._queryset = get_subordinate_groups(request.user, site)
        return formfield


class PagePermissionInlineAdmin(PagePermissionMixin, admin.TabularInline):
    model = PagePermission
    # use special form, so we can override of user and group field
    # form = PagePermissionInlineAdminForm
    classes = ['collapse', 'collapsed']
    fields = ['user', 'group', 'can_add', 'can_change', 'can_delete', 'can_publish', 'can_change_advanced_settings',
              'can_change_permissions', 'can_move_page', 'grant_on',
    ]
    extra = 0  # edit page load time boost
    autocomplete_fields = ['user', 'group']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(can_view=False)

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
        formset_cls = super().get_formset(request, obj=obj, **kwargs)
        queryset = self.get_queryset(request)
        if obj:
            queryset = queryset.filter(page=obj)
        formset_cls._queryset = queryset
        return formset_cls


class ViewRestrictionInlineAdmin(PagePermissionMixin, admin.TabularInline):
    model = PagePermission
    extra = 0  # edit page load time boost
    verbose_name = _("View restriction")
    verbose_name_plural = _("View restrictions")
    fields = ['user', 'group', 'grant_on', 'can_view']
    autocomplete_fields = ['user', 'group']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'can_view':
            formfield.widget = formfield.hidden_widget()
            formfield.initial = True
        return formfield

    def get_queryset(self, request):
        return super().get_queryset(request).filter(can_view=True)


class GlobalPagePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions',
                    'can_change_advanced_settings']
    list_filter = ['can_change', 'can_delete', 'can_publish', 'can_change_permissions',
                   'can_change_advanced_settings']
    fields = ['user', 'group', 'can_add', 'can_change', 'can_delete', 'can_publish', 'can_change_advanced_settings',
              'can_change_permissions', 'can_move_page', 'can_view', 'can_set_as_home', 'sites']
    search_fields = ['user__{}'.format(field) for field in admin_class.search_fields] + ['group__name']
    autocomplete_fields = ['user', 'group']
    filter_horizontal = ['sites']
    list_filter_threshold = 100  # if the number of users and/or groups exceeds this threshold, don't add a filter

    def get_list_filter(self, request):
        list_filter = list(super().get_list_filter(request))
        if Group.objects.count() < self.list_filter_threshold:
            list_filter.insert(0, 'group')
        if get_user_model().objects.count() < self.list_filter_threshold:
            list_filter.insert(0, 'user')
        return list_filter

    def has_add_permission(self, request):
        site = Site.objects.get_current(request)
        return permissions.user_can_add_global_permissions(request.user, site)

    def has_change_permission(self, request, obj=None):
        site = Site.objects.get_current(request)
        return permissions.user_can_change_global_permissions(request.user, site)

    def has_delete_permission(self, request, obj=None):
        site = Site.objects.get_current(request)
        return permissions.user_can_delete_global_permissions(request.user, site)


if get_cms_setting('PERMISSION'):
    admin.site.register(GlobalPagePermission, GlobalPagePermissionAdmin)
    PERMISSION_ADMIN_INLINES.extend([
        ViewRestrictionInlineAdmin,
        PagePermissionInlineAdmin,
    ])
