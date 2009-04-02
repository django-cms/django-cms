from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import File
from django.conf import settings

class FilePlugin(CMSPluginBase):
    model = File
    name = _("File")
    form_template = "file/form.html"
    render_template = "file/plugin.html"
    
    def render(self, context, instance, placeholder):      
        return {'file':instance, 'placeholder':placeholder, 'MEDIA_URL': settings.MEDIA_URL}
    
plugin_pool.register_plugin(FilePlugin)
