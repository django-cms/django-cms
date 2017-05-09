# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import functools

from classytags.core import Tag, Options
from cms.toolbar.utils import get_placeholder_toolbar_js, get_plugin_toolbar_js
from cms.utils.encoder import SafeJSONEncoder
from django import template
from django.utils.safestring import mark_safe

from sekizai.helpers import get_varname

from cms.models import StaticPlaceholder


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
def render_placeholder_toolbar_js(placeholder, render_language, renderer):
    page = placeholder.page
    slot = placeholder.slot
    placeholder_cache = renderer.get_rendered_plugins_cache(placeholder)
    rendered_plugins = placeholder_cache['plugins']
    plugin_parents = placeholder_cache['plugin_parents']
    plugin_children = placeholder_cache['plugin_children']
    plugin_pool = renderer.plugin_pool
    plugin_types = [cls.__name__ for cls in plugin_pool.get_all_plugins(slot, page)]
    allowed_plugins = plugin_types + plugin_pool.get_system_plugins()

    get_toolbar_js = functools.partial(
        get_plugin_toolbar_js,
        request_language=renderer.request_language,
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
        request_language=renderer.request_language,
        render_language=render_language,
        allowed_plugins=allowed_plugins,
    )
    return mark_safe(plugin_js_output + '\n' + placeholder_js_output)


@register.simple_tag(takes_context=True)
def render_cms_structure_js(context, renderer, obj):
    markup_bits = []
    static_placeholders = []
    page_placeholders = obj.rescan_placeholders().values()
    declared_static_placeholders = obj.get_declared_static_placeholders(context)

    for static_placeholder in declared_static_placeholders:
        kwargs = {
            'code': static_placeholder.slot,
            'defaults': {'creation_method': StaticPlaceholder.CREATION_BY_TEMPLATE}
        }

        if static_placeholder.site_bound:
            kwargs['site'] = renderer.site_id
        else:
            kwargs['site_id__isnull'] = True

        static_placeholder = StaticPlaceholder.objects.get_or_create(**kwargs)[0]
        static_placeholders.append(static_placeholder)

    for placeholder in page_placeholders:
        placeholder_js = renderer.render_page_placeholder(obj, placeholder)
        markup_bits.append(placeholder_js)

    for placeholder in static_placeholders:
        placeholder_js = renderer.render_static_placeholder(placeholder)
        markup_bits.append(placeholder_js)
    return mark_safe('\n'.join(markup_bits))


@register.simple_tag(takes_context=True)
def render_plugin_init_js(context, clipboard_plugin):
    renderer = context['cms_renderer']
    plugin_js = renderer.get_plugin_toolbar_js(clipboard_plugin)
    # Add the toolbar javascript for this plugin to the
    # sekizai "js" namespace.
    context[get_varname()]['js'].append('<script>{}</script>'.format(plugin_js))


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
        return "'%s'" % escapejs(rendered.strip())
register.tag(JavascriptString)
