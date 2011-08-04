from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import File
from django.conf import settings

class FilePlugin(CMSPluginBase):
    model = File
    name = _("File")
    render_template = "cms/plugins/file.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):  
        context.update({
            'object':instance, 
            'placeholder':placeholder
        })    
        return context

    def icon_src(self, instance):
        file_icon = instance.get_icon_url()
        if file_icon: return file_icon
        return settings.STATIC_URL + u"cms/images/plugins/file.png"
    
plugin_pool.register_plugin(FilePlugin)
