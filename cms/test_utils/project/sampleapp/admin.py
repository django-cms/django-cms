from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.test_utils.project.sampleapp.models import (
    Category, Picture, SampleAppConfig, SomeEditableModel,
)


class PictureInline(admin.StackedInline):
    model = Picture


class CategoryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]


class SomeEditableAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(Category, CategoryAdmin)
admin.site.register(SampleAppConfig)
admin.site.register(SomeEditableModel, SomeEditableAdmin)
