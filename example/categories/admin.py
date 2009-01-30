from django.contrib import admin
from categories.models import Category
from reversion.admin import VersionAdmin


class CategoryAdmin(VersionAdmin):
    pass

admin.site.register(Category, CategoryAdmin)
