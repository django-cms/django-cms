from cms.admin.placeholderadmin import PlaceholderAdmin
from django.contrib import admin
from cms.test.apps.sampleapp.models import Picture, Category

class PictureInline(admin.StackedInline):
    model = Picture

class CategoryAdmin(PlaceholderAdmin):
    inlines = [PictureInline]

admin.site.register(Category, CategoryAdmin)
