

from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Picture
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings

class PicturePlugin(CMSPluginBase):
    model = Picture
    name = _("Picture")
    form_template = "picture/form.html"
    
    def render(self, context, instance, placeholder):
        request = context['request']
        
        return mark_safe(render_to_string("picture/plugin.html", {'picture':instance, 'placeholder':placeholder}))
    
plugin_pool.register_plugin(PicturePlugin)