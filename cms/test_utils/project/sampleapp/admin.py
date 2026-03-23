from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.utils import GrouperModelAdmin
from cms.test_utils.project.sampleapp.models import (
    Category,
    GrouperModel,
    Picture,
    SampleAppConfig,
    SimpleGrouperModel,
    SomeEditableModel,
)


class PictureInline(admin.StackedInline):
    model = Picture


class CategoryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]


class SomeEditableAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass


class GrouperAdmin(GrouperModelAdmin):
    extra_grouping_fields = ("language",)
    list_display = ("category_name", "content__secret_greeting", "admin_list_actions")

    def can_change_content(self, request, content_obj):
        return getattr(self, "change_content", True)


class SimpleGrouperAdmin(GrouperModelAdmin):
    list_display = ("category_name", "content__secret_greeting", "admin_list_actions")

    def can_change_content(self, request, content_obj):
        return getattr(self, "change_content", True)


admin.site.register(Category, CategoryAdmin)
admin.site.register(SampleAppConfig)
admin.site.register(SomeEditableModel, SomeEditableAdmin)
admin.site.register(GrouperModel, GrouperAdmin)
admin.site.register(SimpleGrouperModel, SimpleGrouperAdmin)
