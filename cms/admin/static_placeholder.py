from django.contrib import admin

from cms.models import StaticPlaceholder
from cms.utils.conf import get_cms_setting


class StaticPlaceholderAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'code', 'site', 'creation_method')
    search_fields = ('name', 'code',)
    exclude = ('creation_method',)
    list_filter = ('creation_method', 'site')


if not get_cms_setting("HIDE_LEGACY_FEATURES"):
    admin.site.register(StaticPlaceholder, StaticPlaceholderAdmin)
