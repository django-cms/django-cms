from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.utils import GrouperModelAdmin
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
    model = GrouperModel
    extra_grouping_fields = ("language",)



admin.site.register(Category, CategoryAdmin)
admin.site.register(SampleAppConfig)
admin.site.register(SomeEditableModel, SomeEditableAdmin)
admin.site.register(Gro)

