from django.utils.translation import ugettext_lazy as _
from models import Link
from cms.settings import CMS_MEDIA_URL
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase


class LinkPlugin(CMSPluginBase):
    model = Link
    name = _("Link")
    render_template = "cms/plugins/link.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):
        if instance.url:
            link = instance.url
        elif instance.page_link:
            link = instance.page_link.get_absolute_url()
        else:
            link = ""
        context.update({
            'name':instance.name,
            'link':link, 
            'placeholder':placeholder,
            'object':instance
        })
        return context 
        
    def icon_src(self, instance):
        return CMS_MEDIA_URL + u"images/plugins/link.png"
    
plugin_pool.register_plugin(LinkPlugin)