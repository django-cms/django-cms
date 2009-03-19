from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Text
from cms.plugins.text.forms import TextForm

class TextPlugin(CMSPluginBase):
    model = Text
    name = _("Text")
    form = TextForm
    render_template = "text/plugin.html"
    
    def render(self, context, instance, placeholder):
        return {'body':instance.body,}
    
plugin_pool.register_plugin(TextPlugin)