from cms.admin.placeholderadmin import PlaceholderAdmin
from django.contrib import admin
from testapp.sampleapp.models import Picture, Category

class PictureInline(admin.StackedInline):
    model = Picture

class CategoryAdmin(PlaceholderAdmin):
    inlines = [PictureInline]

admin.site.register(Category, CategoryAdmin)