from django import template
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def js(value):
    return simplejson.dumps(value, cls=DjangoJSONEncoder)
