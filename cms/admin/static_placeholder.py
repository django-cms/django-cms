from cms.models import StaticPlaceholder
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.db import models
from cms.admin.placeholderadmin import PlaceholderAdmin


class StaticPlaceholderAdmin(PlaceholderAdmin):
    list_display = ('name', 'code', 'linked_plugins_count', 'creation_method')
    search_fields = ('name', 'code',)
    exclude = ('creation_method',)
    list_filter = ('creation_method',)

    def queryset(self, request):
        return super(StaticPlaceholderAdmin, self).queryset(request).annotate(
            linked_plugins_count=models.Count('linked_plugins'))

    def linked_plugins_count(self, obj):
        return getattr(obj, 'linked_plugins_count', '-')

    linked_plugins_count.short_description = _('linked plugins')
    linked_plugins_count.admin_order_field = 'linked_plugins_count'

    def post_add_plugin(self, request, placeholder, plugin):
        self.mark_dirty(placeholder)

    def post_copy_plugins(self, request, source_placeholder, target_placeholder, plugins):
        self.mark_dirty(target_placeholder)

    def post_edit_plugin(self, request, plugin):
        self.mark_dirty(plugin.placeholder)

    def post_move_plugin(self, request, plugin):
        self.mark_dirty(plugin.placeholder)

    def post_delete_plugin(self, request, plugin):
        self.mark_dirty(plugin.placeholder)

    def post_clear_placeholder(self, request, placeholder):
        self.mark_dirty(placeholder)

    @staticmethod
    def mark_dirty(placeholder):
        placeholder.static_draft.update(dirty=True)


admin.site.register(StaticPlaceholder, StaticPlaceholderAdmin)
