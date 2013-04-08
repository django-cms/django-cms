# -*- coding: utf-8 -*-
from distutils.version import LooseVersion

from classytags.core import Tag, Options
import django
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import javascript_quote

DJANGO_1_4 = LooseVersion(django.get_version()) < LooseVersion('1.5')

if DJANGO_1_4:
    from django.utils import simplejson as json
else:
    import json

register = template.Library()

@register.filter
def js(value):
    return json.dumps(value, cls=DjangoJSONEncoder)

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
