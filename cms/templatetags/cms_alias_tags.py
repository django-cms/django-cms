import warnings

from django import template
from django.utils.safestring import mark_safe

from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
from cms.utils.plugins import downcast_plugins, get_plugins_as_layered_tree

register = template.Library()


@register.simple_tag(takes_context=True)
def render_alias_plugin(context, instance):
    warnings.warn(
        'AliasPlugin is deprecated, '
        'and it will be removed; '
        'please use the package djangocms-alias instead',
        RemovedInDjangoCMS43Warning
    )

    request = context['request']
    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.content_renderer

    if instance.plugin:
        plugins = instance.plugin.get_descendants()
        plugins = [instance.plugin] + list(plugins)
        plugins = downcast_plugins(plugins, request=request)
        plugins = list(plugins)
        plugins = get_plugins_as_layered_tree(plugins)
        content = renderer.render_plugin(
            instance=plugins[0],
            context=context,
            editable=False,
        )
        return mark_safe(content)

    if instance.alias_placeholder:
        content = renderer.render_placeholder(
            placeholder=instance.alias_placeholder,
            context=context,
            editable=False,
        )
        return mark_safe(content)
    return ''
