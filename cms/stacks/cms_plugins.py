from django.utils.translation import ugettext_lazy as _

from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.plugin_rendering import render_placeholder

from cms.stacks.models import StackLink, Stack


class StackPlugin(CMSPluginBase):
    model = StackLink
    name = _("Stack")
    render_template = "cms/plugins/stacks.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        html_content = render_placeholder(instance.stack.content, context)
        context.update({
            'instance': instance,
            'placeholder': placeholder,
            'content': html_content,
        })
        return context


plugin_pool.register_plugin(StackPlugin)
