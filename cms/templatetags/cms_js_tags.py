# -*- coding: utf-8 -*-
import json
import functools

from classytags.core import Tag, Options
from cms.toolbar.utils import get_placeholder_toolbar_js, get_plugin_toolbar_js
from cms.utils.encoder import SafeJSONEncoder
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter('json')
def json_filter(value):
    """
    Returns the JSON representation of ``value`` in a safe manner.
    """
    return mark_safe(json.dumps(value, cls=SafeJSONEncoder))


@register.filter
def bool(value):
    if value:
        return 'true'
    else:
        return 'false'


@register.simple_tag(takes_context=False)
def render_placeholder_toolbar_js(placeholder, render_language, content_renderer):
    page = placeholder.page
    slot = placeholder.slot
    placeholder_cache = content_renderer.get_rendered_plugins_cache(placeholder)
    rendered_plugins = placeholder_cache['plugins']
    plugin_parents = placeholder_cache['plugin_parents']
    plugin_children = placeholder_cache['plugin_children']
    plugin_pool = content_renderer.plugin_pool
    plugin_types = [cls.__name__ for cls in plugin_pool.get_all_plugins(slot, page)]
    allowed_plugins = plugin_types + plugin_pool.get_system_plugins()

    get_toolbar_js = functools.partial(
        get_plugin_toolbar_js,
        request_language=content_renderer.request_language,
    )

    def _render_plugin_js(plugin):
        try:
            child_classes = plugin_children[plugin.plugin_type]
        except KeyError:
            plugin_class = plugin_pool.plugins[plugin.plugin_type]
            child_classes = plugin_class.get_child_classes(slot=slot, page=page, instance=plugin)

        try:
            parent_classes = plugin_parents[plugin.plugin_type]
        except KeyError:
            plugin_class = plugin_pool.plugins[plugin.plugin_type]
            parent_classes = plugin_class.get_parent_classes(slot=slot, page=page, instance=plugin)

        content = get_toolbar_js(
            plugin,
            children=child_classes,
            parents=parent_classes,
        )
        return content

    plugin_js_output = ''.join(_render_plugin_js(plugin) for plugin in rendered_plugins)
    placeholder_js_output = get_placeholder_toolbar_js(
        placeholder=placeholder,
        request_language=content_renderer.request_language,
        render_language=render_language,
        allowed_plugins=allowed_plugins,
    )
    return mark_safe(plugin_js_output + '\n' + placeholder_js_output)


class JavascriptString(Tag):
    name = 'javascript_string'
    options = Options(
        blocks=[
            ('end_javascript_string', 'nodelist'),
        ]
    )

    def render_tag(self, context, **kwargs):
        try:
            from django.utils.html import escapejs
        except ImportError:
            from django.utils.text import javascript_quote as escapejs
        rendered = self.nodelist.render(context)
        return u"'%s'" % escapejs(rendered.strip())
register.tag(JavascriptString)
