from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.plugins.column.models import Column
from django.utils.translation import ugettext_lazy as _

class ColumnPlugin(CMSPluginBase):
    model = Column
    name = _("Columns")
    render_template = "cms/columns/columns.html"

    def render(self, context, instance, placeholder):
        placeholders = instance.placeholders.all()
        context.update({
            'placeholders': placeholders,
            'instance': instance,
        })
        return context


plugin_pool.register_plugin(ColumnPlugin)
