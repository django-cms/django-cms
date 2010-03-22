from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Flash
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from cms.plugins.flash.forms import FlashForm

class FlashPlugin(CMSPluginBase):
    model = Flash
    name = _("Flash")
    form = FlashForm
    
    class PluginMedia:
        js = ('http://ajax.googleapis.com/ajax/libs/swfobject/2.1/swfobject.js',)
    
    render_template = "cms/plugins/flash.html"
    def render(self, context, instance, placeholder):
        context.update({
            'object': instance,
            'placeholder':placeholder,
        })
        return context
    
plugin_pool.register_plugin(FlashPlugin)