from django.conf import settings
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.googlemap.models import GoogleMap
from django.forms.widgets import Media

class GoogleMapPlugin(CMSPluginBase):
    model = GoogleMap
    name = _("Google Map")
    render_template = "cms/plugins/googlemap.html"
    
    def render(self, context, instance, placeholder):
        context.update({
            'object':instance, 
            'placeholder':placeholder, 
        })
        return context

plugin_pool.register_plugin(GoogleMapPlugin)