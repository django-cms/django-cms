# -*- coding: utf-8 -*-
from django import template
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def js(value):
    return simplejson.dumps(value, cls=DjangoJSONEncoder)

@register.filter
def bool(value):
    return value and "true" or "false" 
        
@register.filter
def js_string(value):
    """Escape `value` to get a safe string for javascript"""
    return simplejson.dumps('%s' % value).replace("'", "\\'").replace('"', '\\"')