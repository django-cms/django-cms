from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.conf import settings
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.plugins.link.forms import LinkForm
from .models import Link

class LinkPlugin(CMSPluginBase):
    model = Link
    form = LinkForm
    name = _("Link")
    render_template = "cms/plugins/link.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        context.update({
            'name': instance.name,
            'link': instance.link,
            'target': instance.target,
            'placeholder': placeholder,
            'object': instance
        })
        return context

    def icon_src(self, instance):
        return settings.STATIC_URL + u"cms/img/icons/plugins/link.png"

plugin_pool.register_plugin(LinkPlugin)
