from django.contrib import admin
from stacks.models import Stack
from cms.admin.placeholderadmin import PlaceholderAdmin


class StackAdmin(PlaceholderAdmin):
    list_display = ('name', 'code',)
    search_fields = ('name', 'code',)


admin.site.register(Stack, StackAdmin)
