from django.contrib import admin

from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.test_utils.project.sampleapp.models import Category, Picture, SampleAppConfig


class PictureInline(admin.StackedInline):
    model = Picture


@admin.register(Category)
class CategoryAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    inlines = [PictureInline]


admin.site.register(SampleAppConfig)
