from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.test_utils.project.sampleapp.models import (
    Category,
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

admin.site.register(SampleAppConfig)
