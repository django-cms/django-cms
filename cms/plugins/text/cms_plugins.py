

from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Text

class TextPlugin(CMSPluginBase):
    model = Text
    name = _("text")
    
    def render(self, request):
        return "hello world"
    
plugin_pool.register_plugin(TextPlugin)