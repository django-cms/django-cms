from django.contrib import admin

from cms.test_utils.project.sampleapp.models import Picture, Category, SampleAppConfig


class PictureInline(admin.StackedInline):
    model = Picture


class CategoryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]

admin.site.register(Category, CategoryAdmin)
admin.site.register(SampleAppConfig)
