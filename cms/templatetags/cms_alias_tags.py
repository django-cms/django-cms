# -*- coding: utf-8 -*-
from django import template
from django.utils.safestring import mark_safe

from cms.utils.plugins import downcast_plugins, build_plugin_tree


register = template.Library()


@register.simple_tag(takes_context=True)
def render_alias_plugin(context, instance):
    renderer = context.get('cms_content_renderer')

    if instance.plugin:
        plugins = instance.plugin.get_descendants().order_by('placeholder', 'path')
        plugins = [instance.plugin] + list(plugins)
        plugins = downcast_plugins(plugins, request=renderer.request)
        plugins = list(plugins)
        plugins[0].parent_id = None
        plugins = build_plugin_tree(plugins)
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
