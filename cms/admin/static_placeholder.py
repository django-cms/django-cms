from django.contrib import admin

from cms.models import StaticPlaceholder


class StaticPlaceholderAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'code', 'site', 'creation_method')
    search_fields = ('name', 'code',)
    exclude = ('creation_method',)
    list_filter = ('creation_method', 'site')


admin.site.register(StaticPlaceholder, StaticPlaceholderAdmin)
