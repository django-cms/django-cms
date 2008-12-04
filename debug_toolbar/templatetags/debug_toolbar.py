from django import template
from django.utils import simplejson

register = template.Library()

register.filter('jsonencode', simplejson.dumps)