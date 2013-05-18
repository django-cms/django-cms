from django.utils.safestring import mark_safe
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugin_rendering import render_plugins
from stacks.fields import StackSearchField
from stacks.models import StackLink
from cms.plugins.utils import get_plugins


class StackPlugin(CMSPluginBase):
    model = StackLink
    name = _("Stack")
    render_template = "cms/plugins/stacks.html"
    admin_preview = False

    def render(self, context, instance, placeholder):
        # TODO: once we drop 2.3.x support we can just use the "render_plugin" templatetag
        #       instead of rendering html here.
        plugins = get_plugins(context['request'], instance.stack.content)
        processors = ()
        html_content = mark_safe(u"".join(render_plugins(plugins, context, placeholder, processors)))
        context.update({
            'instance': instance,
            'placeholder': placeholder,
            'content': html_content,
        })
        return context

    def formfield_for_dbfield(self, db_field, request=None, **kwargs):
        if db_field.name == "stack":
            return StackSearchField(**kwargs)
        return super(StackPlugin, self).formfield_for_dbfield(db_field, request=request, **kwargs)


plugin_pool.register_plugin(StackPlugin)
