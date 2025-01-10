import json

from classytags.core import Options, Tag
from django import template
from django.utils.safestring import mark_safe
from sekizai.helpers import get_varname

from cms.utils.encoder import SafeJSONEncoder
from cms.utils.placeholder import (
    get_declared_placeholders_for_obj,
    rescan_placeholders_for_obj,
)

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
    obj_placeholders_by_slot = rescan_placeholders_for_obj(obj)
    declared_placeholders = get_declared_placeholders_for_obj(obj)
    try:
        lang = context["request"].toolbar.request_language
    except AttributeError:
        lang = None

    for placeholder_node in declared_placeholders:
        obj_placeholder = obj_placeholders_by_slot.get(placeholder_node.slot)

        if obj_placeholder:
            placeholder_js = renderer.render_placeholder(obj_placeholder, language=lang, page=obj)
            markup_bits.append(placeholder_js)


    # https://github.com/django-cms/django-cms/commit/0f12156c8ed85914d4e3b14b30bce87becefe92b
    static_placeholders = []
    # declared_static_placeholders = cms_page.get_declared_static_placeholders(context)

    # djangocms-alias is hacked in here, needs a configuration mechanism tuned in
    #  Potentially a configure Page Sticky placeholders
    #   By default it's empty.
    # A 3rd party package will add the config.
    # Needs to be like: get_declared_placeholders_for_obj
    #
    # Also needs to be decided if the Alias can be edited inline or if the link takes the user off to edit the alias.


    from djangocms_alias.models import Alias

    # HACK to test by code
    Alias.objects.all().update(static_code="static")

    alias_set = Alias.objects.filter(static_code="static")

    for alias in alias_set:

        alias_placeholder = alias.get_placeholder(language="en", show_draft_content=True)
        # if obj_placeholder:
        #     placeholder_js = renderer.render_placeholder(obj_placeholder, language=None, page=obj)
        #     markup_bits.append(placeholder_js)
        static_placeholders.append(alias_placeholder)

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
    context[get_varname()]['js'].append(f'<script data-cms>{plugin_js}</script>')


@register.tag(name="javascript_string")
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
