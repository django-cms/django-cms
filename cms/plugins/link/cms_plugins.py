from django.utils.translation import ugettext_lazy as _
from models import Link
from cms.settings import CMS_MEDIA_URL
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.plugins.link.forms import LinkForm


class LinkPlugin(CMSPluginBase):
    model = Link
    form = LinkForm
    name = _("Link")
    render_template = "cms/plugins/link.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):
        if instance.mailto:
            link = "mailto:%s" % instance.mailto
        elif instance.url:
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
    
    def get_form(self, request, obj=None, **kwargs):
        Form = super(LinkPlugin, self).get_form(request, obj, **kwargs)
        
        # this is bit tricky, since i don't wont override add_view and 
        # change_view 
        class FakeForm(object):
            def __init__(self, Form, site):
                self.Form = Form
                self.site = site
                
                # base fields are required to be in this fake class, this may
                # do some troubles, with new versions of django, if there will
                # be something more required
                self.base_fields = Form.base_fields
            
            def __call__(self, *args, **kwargs):
                # instanciate the form on call
                form = self.Form(*args, **kwargs)
                # tell form we are on this site
                form.for_site(self.site)
                return form
            
        return FakeForm(Form, self.cms_plugin_instance.page.site) 
        
    def icon_src(self, instance):
        return CMS_MEDIA_URL + u"images/plugins/link.png"
    
plugin_pool.register_plugin(LinkPlugin)