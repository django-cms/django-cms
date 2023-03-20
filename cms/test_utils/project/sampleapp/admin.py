from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.utils import GrouperModelAdmin
from cms.test_utils.project.sampleapp.forms import GrouperAdminForm
from cms.test_utils.project.sampleapp.models import (
    Category, GrouperModel, Picture, SampleAppConfig, SomeEditableModel,
)


class PictureInline(admin.StackedInline):
    model = Picture


class CategoryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]


class SomeEditableAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass


class GrouperAdmin(GrouperModelAdmin):
    form = GrouperAdminForm
    extra_grouping_fields = ("language",)
    list_display = ("category_name", "content: secret_greeting",)


admin.site.register(Category, CategoryAdmin)
admin.site.register(SampleAppConfig)
admin.site.register(SomeEditableModel, SomeEditableAdmin)
admin.site.register(GrouperModel, GrouperAdmin)
