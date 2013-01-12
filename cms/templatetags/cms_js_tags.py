# -*- coding: utf-8 -*-
from classytags.core import Tag, Options
import django
from django import template
from django.core.serializers import json
from django.utils import simplejson
from django.utils.text import javascript_quote

jsonparser = json.json if django.get_version() >= '1.5' else simplejson

register = template.Library()

@register.filter
def js(value):
    jsonparser.dumps(value, cls=json.DjangoJSONEncoder)

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
