# -*- coding: utf-8 -*-
from classytags.core import Tag, Options
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson
from django.utils.text import javascript_quote

register = template.Library()

@register.filter
def js(value):
    return simplejson.dumps(value, cls=DjangoJSONEncoder)

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
