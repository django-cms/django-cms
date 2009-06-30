from django.utils.translation import ugettext_lazy as _
from django import forms
from models import Link
from cms.settings import CMS_MEDIA_URL
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.models import Page


class LinkPluginForm(forms.ModelForm):
    # change field, so we don't see add page icon in admin
    page_link = forms.ModelChoiceField(Page.objects, label=_('Page'), required=False)
    
    class Meta:
        model = Link


class LinkPlugin(CMSPluginBase):
    model = Link
    name = _("Link")
    render_template = "cms/plugins/link.html"
    text_enabled = True
    
    form = LinkPluginForm
    
    def render(self, context, instance, placeholder):
        if instance.url:
            link = instance.url
        elif instance.page_link:
            link = instance.page_link.get_absolute_url()
        else:
            link = ""
        return {'name':instance.name,
                'link':link, 
                'placeholder':placeholder}
        
    def icon_src(self, instance):
        return CMS_MEDIA_URL + u"images/plugins/link.png"
    
plugin_pool.register_plugin(LinkPlugin)