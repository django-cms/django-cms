# -*- coding: utf-8 -*-
from classytags.core import Tag, Options
from cms.utils.encoder import SafeJSONEncoder
from cms.utils.compat import DJANGO_1_4
from django import template
from django.utils.text import javascript_quote
from django.utils.safestring import mark_safe
if DJANGO_1_4:
    from django.utils import simplejson as json
else:
    import json
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
        rendered = self.nodelist.render(context)
        return u"'%s'" % javascript_quote(rendered.strip())
register.tag(JavascriptString)
