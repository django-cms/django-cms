from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.picture.models import Picture

class PicturePlugin(CMSPluginBase):
    model = Picture
    name = _("Picture")
    render_template = "cms/plugins/picture.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):
        return {'picture':instance, 'placeholder':placeholder}
    
plugin_pool.register_plugin(PicturePlugin)