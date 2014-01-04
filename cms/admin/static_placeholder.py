from cms.models import StaticPlaceholder
from django.contrib import admin
from cms.admin.placeholderadmin import PlaceholderAdmin


class StaticPlaceholderAdmin(PlaceholderAdmin):
    list_display = ('name', 'code', 'creation_method')
    search_fields = ('name', 'code',)
    exclude = ('creation_method',)
    list_filter = ('creation_method',)

    def post_add_plugin(self, request, placeholder, plugin):
        self.mark_dirty(placeholder)

    def post_copy_plugins(self, request, source_placeholder, target_placeholder, plugins):
        self.mark_dirty(target_placeholder)

    def post_edit_plugin(self, request, plugin):
        self.mark_dirty(plugin.placeholder)

    def post_move_plugin(self, request, source_placeholder, target_placeholder, plugin):
        self.mark_dirty(source_placeholder)
        self.mark_dirty(target_placeholder)

    def post_delete_plugin(self, request, plugin):
        self.mark_dirty(plugin.placeholder)

    def post_clear_placeholder(self, request, placeholder):
        self.mark_dirty(placeholder)

    @staticmethod
    def mark_dirty(placeholder):
        placeholder.static_draft.update(dirty=True)


admin.site.register(StaticPlaceholder, StaticPlaceholderAdmin)
