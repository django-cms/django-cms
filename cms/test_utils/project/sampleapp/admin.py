from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.utils import GrouperModelAdmin
from cms.test_utils.project.sampleapp.models import (
    Category,
    GrouperModel,
    Picture,
    SampleAppConfig,
    SomeEditableModel,
)


class PictureInline(admin.StackedInline):
    model = Picture


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]


@admin.register(SomeEditableModel)
class SomeEditableAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass


@admin.register(GrouperModel)
class GrouperAdmin(GrouperModelAdmin):
    extra_grouping_fields = ("language",)
    list_display = ("category_name", "content__secret_greeting", "admin_list_actions")

    def can_change_content(self, request, content_obj):
        return getattr(self, "change_content", True)


admin.site.register(SampleAppConfig)
