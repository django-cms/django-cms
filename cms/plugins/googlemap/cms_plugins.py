from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.googlemap.models import GoogleMap
from cms.plugins.googlemap.settings import GOOGLE_MAPS_API_KEY
from cms.plugins.googlemap import settings
from django.forms.widgets import Media

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
    
    def get_plugin_media(self, request, plugin):
        return Media(js = ('http://maps.google.com/maps?file=api&amp;v=2&amp;key=%s&amp;hl=%s' % (settings.GOOGLE_MAPS_API_KEY, request.LANGUAGE_CODE),))
 
plugin_pool.register_plugin(GoogleMapPlugin)