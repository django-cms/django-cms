from cms.admin.placeholderadmin import PlaceholderAdminMixin
from django.contrib import admin
from cms.test_utils.project.sampleapp.models import Picture, Category


class PictureInline(admin.StackedInline):
    model = Picture


class CategoryAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    inlines = [PictureInline]

admin.site.register(Category, CategoryAdmin)
