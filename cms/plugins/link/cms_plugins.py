from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.conf import settings
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.plugins.link.forms import LinkForm
from models import Link

class LinkPlugin(CMSPluginBase):
    model = Link
    form = LinkForm
    name = _("Link")
    render_template = "cms/plugins/link.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):
        if instance.mailto:
            link = u"mailto:%s" % instance.mailto
        elif instance.url:
            link = instance.url
        elif instance.page_link:
            link = instance.page_link.get_absolute_url()
        else:
            link = ""
        context.update({
            'name': instance.name,
            'link': link, 
            'target':instance.target,
            'placeholder': placeholder,
            'object': instance
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
        # TODO: Make sure this works
        if self.cms_plugin_instance.page and self.cms_plugin_instance.page.site:
            site = self.cms_plugin_instance.page.site
        elif self.page and self.page.site:
            site = self.page.site
        else:
            # this might NOT give the result you expect
            site = Site.objects.get_current()
        return FakeForm(Form, site)
        
    def icon_src(self, instance):
        return settings.STATIC_URL + u"cms/images/plugins/link.png"
    
plugin_pool.register_plugin(LinkPlugin)
