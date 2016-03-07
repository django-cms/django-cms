# -*- coding: utf-8 -*-
import json

from classytags.core import Tag, Options
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
