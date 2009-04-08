from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Link
from cms.plugins.text.forms import TextForm

class LinkPlugin(CMSPluginBase):
    model = Link
    name = _("Link")
    render_template = "cms/plugins/link.html"
    
    def render(self, context, instance, placeholder):
        if instance.link:
            link = instance.link
        if instance.page:
            link = instance.page.get_absolute_url()
        return {'name':instance.name,
                'link':link, 
                'placeholder':placeholder}
    
plugin_pool.register_plugin(LinkPlugin)