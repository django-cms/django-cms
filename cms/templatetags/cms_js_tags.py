# -*- coding: utf-8 -*-
import warnings
from classytags.core import Tag, Options
from cms.utils.compat import DJANGO_1_4
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import conditional_escape
from django.utils.text import javascript_quote
from django.utils.safestring import mark_safe
if DJANGO_1_4:
    from django.utils import simplejson as json
else:
    import json
register = template.Library()


@register.filter
def js(value):
    warnings.warn("The template filter '...|js' is vulnerable to XSS attacks, please use '...|json' instead.",
                  DeprecationWarning, stacklevel=2)
    return json.dumps(value, cls=DjangoJSONEncoder)


class SafeJSONEncoder(DjangoJSONEncoder):
    def _recursive_escape(self, o, esc=conditional_escape):
        if isinstance(o, dict):
            return type(o)((esc(k), self._recursive_escape(v)) for (k, v) in o.iteritems())
        if isinstance(o, (list, tuple)):
            return type(o)(self._recursive_escape(v) for v in o)
        try:
            return type(o)(esc(o))
        except ValueError:
            return esc(o)

    def encode(self, o):
        value = self._recursive_escape(o)
        return super(SafeJSONEncoder, self).encode(value)


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
