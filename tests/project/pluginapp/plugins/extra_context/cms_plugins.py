from django.utils.translation import ugettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from project.pluginapp.plugins.extra_context.models import ExtraContextPluginModel

class ExtraContextPlugin(CMSPluginBase):
    model = ExtraContextPluginModel
    name = _("Extra Context")
    render_template = "extra_context_plugin.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        return context
    
plugin_pool.register_plugin(ExtraContextPlugin)
