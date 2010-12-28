from django.contrib import admin
from example.sampleapp.models import Picture, Category
from cms.admin.placeholderadmin import PlaceholderAdmin

class PictureInline(admin.StackedInline):
    model = Picture

class CategoryAdmin(PlaceholderAdmin):
    inlines = [PictureInline]

admin.site.register(Category, CategoryAdmin)