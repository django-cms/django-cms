from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.googlemap.models import GoogleMap
from cms.plugins.googlemap.settings import GOOGLE_MAPS_API_KEY

class GoogleMapPlugin(CMSPluginBase):
    model = GoogleMap
    name = _("Google Map")
    render_template = "cms/plugins/googlemap.html"
    
    def render(self, context, instance, placeholder):
        if 'GOOGLE_MAPS_API_KEY' in context:
            key = context['GOOGLE_MAPS_API_KEY']
        else:
            key = GOOGLE_MAPS_API_KEY
        context.update({
            'object':instance, 
            'placeholder':placeholder, 
            'GOOGLE_MAPS_API_KEY':key
        })
        return context
 
plugin_pool.register_plugin(GoogleMapPlugin)