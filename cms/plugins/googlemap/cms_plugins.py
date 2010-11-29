from django.conf import settings
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.googlemap.models import GoogleMap
from cms.plugins.googlemap.settings import GOOGLE_MAPS_API_KEY
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
    
    def get_plugin_media(self, request, context, plugin):
        if 'GOOGLE_MAPS_API_KEY' in context:
            key = context['GOOGLE_MAPS_API_KEY']
        else:
            key = GOOGLE_MAPS_API_KEY
        lang = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE[0:2])
        return Media(js = ('http://maps.google.com/maps?file=api&amp;v=2&amp;key=%s&amp;hl=%s' % (key, lang),))

plugin_pool.register_plugin(GoogleMapPlugin)