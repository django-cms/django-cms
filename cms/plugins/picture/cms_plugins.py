from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.picture.models import Picture
from cms.settings import CMS_MEDIA_URL

class PicturePlugin(CMSPluginBase):
    model = Picture
    name = _("Picture")
    render_template = "cms/plugins/picture.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):
        return {'picture':instance, 'placeholder':placeholder}
    
    def icon_src(self, instance):
        # TODO - possibly use 'instance' and provide a thumbnail image
        return CMS_MEDIA_URL + u"images/plugins/image.png"
 
plugin_pool.register_plugin(PicturePlugin)