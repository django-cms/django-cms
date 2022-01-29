import json

from classytags.core import Options, Tag
from django import template
from django.utils.safestring import mark_safe
from sekizai.helpers import get_varname

from cms.models import StaticPlaceholder
from cms.utils.encoder import SafeJSONEncoder

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


@register.simple_tag(takes_context=True)
def render_cms_structure_js(context, renderer, obj):
    markup_bits = []
    static_placeholders = []
    page_placeholders_by_slot = obj.rescan_placeholders()
    declared_static_placeholders = obj.get_declared_static_placeholders(context)

    for static_placeholder in declared_static_placeholders:
        kwargs = {
            'code': static_placeholder.slot,
            'defaults': {'creation_method': StaticPlaceholder.CREATION_BY_TEMPLATE}
        }

        if static_placeholder.site_bound:
            kwargs['site'] = renderer.current_site
        else:
            kwargs['site_id__isnull'] = True

        static_placeholder = StaticPlaceholder.objects.get_or_create(**kwargs)[0]
        static_placeholders.append(static_placeholder)

    for placeholder_node in obj.get_declared_placeholders():
        page_placeholder = page_placeholders_by_slot.get(placeholder_node.slot)

        if page_placeholder:
            placeholder_js = renderer.render_page_placeholder(obj, page_placeholder)
            markup_bits.append(placeholder_js)

    for placeholder in static_placeholders:
        placeholder_js = renderer.render_static_placeholder(placeholder)
        markup_bits.append(placeholder_js)
    return mark_safe('\n'.join(markup_bits))


@register.simple_tag(takes_context=True)
def render_plugin_init_js(context, plugin):
    renderer = context['cms_renderer']
    plugin_js = renderer.get_plugin_toolbar_js(plugin)
    # Add the toolbar javascript for this plugin to the
    # sekizai "js" namespace.
    context[get_varname()]['js'].append('<script data-cms>{}</script>'.format(plugin_js))


class JavascriptString(Tag):
    name = 'javascript_string'
    options = Options(
        blocks=[
            ('end_javascript_string', 'nodelist'),
        ]
    )

    def render_tag(self, context, **kwargs):
        from django.utils.html import escapejs

        rendered = self.nodelist.render(context)
        return "'%s'" % escapejs(rendered.strip())


register.tag(JavascriptString)
