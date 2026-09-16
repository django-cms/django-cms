from django.utils.translation import gettext as _

from cms.core.models.plugin import CMSPlugin
from cms.core.plugin_base import CMSPluginBase
from cms.core.plugin_pool import plugin_pool


class ExtraContextPlugin(CMSPluginBase):
    model = CMSPlugin
    name = _("Extra Context")
    render_template = "extra_context_plugin.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        return context


plugin_pool.register_plugin(ExtraContextPlugin)
