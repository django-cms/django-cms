from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.plugins.column.models import Column, ColumnPlaceholder
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class PlaceholderInline(admin.TabularInline):
    model = ColumnPlaceholder


class ColumnPlugin(CMSPluginBase):
    model = Column
    name = _("Columns")
    render_template = "cms/plugins/column.html"
    inlines = [PlaceholderInline]
    frontend_edit_template = "cms/plugins/column_frontend_edit.html"

    def render(self, context, instance, placeholder):
        placeholders = instance.placeholder_inlines.all()
        context.update({
            'placeholders': placeholders,
            'instance': instance,
        })
        return context

plugin_pool.register_plugin(ColumnPlugin)
