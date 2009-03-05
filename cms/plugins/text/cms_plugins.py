

from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Text
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from cms.plugins.text.forms import TextForm

class TextPlugin(CMSPluginBase):
    model = Text
    name = _("Text")
    form = TextForm
    
    def render(self, request, instance, placeholder):
        return mark_safe(render_to_string("text/plugin.html", {'body':instance.body,}))
        return instance.body
    
plugin_pool.register_plugin(TextPlugin)