from classytags.arguments import Argument
from classytags.core import Tag, Options
from django import template

from cms.plugin_rendering import render_placeholder

from cms.stacks.models import Stack

register = template.Library()


class StackNode(Tag):
    name = 'stack'
    options = Options(
        Argument('code', required=True),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, code, varname):
        raise DeprecationWarning('stack templatetag is deprecated. Use static_placeholder instead.')


register.tag(StackNode)
