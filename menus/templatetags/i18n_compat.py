from classytags.arguments import Argument
from classytags.core import Tag, Options
from django import template

register = template.Library()

@register.tag
def language(parser, token):
    try:
        from django.templatetags.i18n import language
    except ImportError:
        from i18nurls.templatetags.i18nurls import language
    return language(parser, token)

