from cms.plugin_base import CMSPagePluginBase
from cms.plugin_pool import plugin_pool
from .models import LinkModel


class PageFieldTestPlugin(CMSPagePluginBase):
    model = LinkModel
    name = "Dumb Test Plugin. It does nothing."
    render_template = ""
    admin_preview = False
    render_plugin = False

    def render(self, context, instance, placeholder):
        return context

plugin_pool.register_plugin(PageFieldTestPlugin)
