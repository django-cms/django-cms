from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.context import Context
from models import SnippetPtr

class SnippetPlugin(CMSPluginBase):
    model = SnippetPtr
    name = _("Snippet")
    render_template = "cms/plugins/snippet.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        context.update({
            'placeholder':placeholder,
            'object':instance,
        })
        try:
            if instance.snippet.template:
                t = template.loader.get_template(instance.snippet.template)
                context.update({'html': mark_safe(instance.snippet.html)})
                content = t.render(Context(context))
            else:
                t = template.Template(instance.snippet.html)
                content = t.render(Context(context))
        except template.TemplateDoesNotExist, e:
            content = _('Template %(template)s does not exist.') % {'template': instance.snippet.template}
        except Exception, e:
            content = str(e)
        context.update({
            'content': mark_safe(content),
        })
        return context

    def icon_src(self, instance):
        return settings.STATIC_URL + u"cms/images/plugins/snippet.png"

plugin_pool.register_plugin(SnippetPlugin)
