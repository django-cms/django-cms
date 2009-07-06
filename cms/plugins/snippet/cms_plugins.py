from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.settings import CMS_MEDIA_URL
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.context import RequestContext, Context
from models import SnippetPtr

class SnippetPlugin(CMSPluginBase):
    model = SnippetPtr
    name = _("Snippet")
    render_template = "cms/plugins/snippet.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        t = template.Template(instance.snippet.html)
        try:
            content = t.render(Context(context))
        except Exception, e:
            content = str(e)
        context.update({
            'content': mark_safe(content),
            'placeholder':placeholder,
            'object':instance,
        })
        return context

    def icon_src(self, instance):
        return CMS_MEDIA_URL + u"images/plugins/snippet.png"

plugin_pool.register_plugin(SnippetPlugin)
