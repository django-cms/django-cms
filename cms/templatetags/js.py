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
        
