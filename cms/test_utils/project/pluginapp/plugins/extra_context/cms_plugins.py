from django.utils.translation import gettext as _

from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool


class ExtraContextPlugin(CMSPluginBase):
    model = CMSPlugin
    name = _("Extra Context")
    render_template = "extra_context_plugin.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        return context


plugin_pool.register_plugin(ExtraContextPlugin)
