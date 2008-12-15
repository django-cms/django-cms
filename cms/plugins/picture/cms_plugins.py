

from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Picture

class PicturePlugin(CMSPluginBase):
    model = Picture
    name = _("Picture")
    form_template = "picture/form.html"
    
    def render(self, request):
        return "hello world"
    
plugin_pool.register_plugin(PicturePlugin)