from classytags.arguments import Argument
from classytags.core import Tag, Options
from django import template
from django.utils.safestring import mark_safe
from cms.plugin_rendering import render_plugins
from cms.plugins.utils import get_plugins
from stacks import models as stack_models
from stacks.models import Stack

register = template.Library()


class StackNode(Tag):
    name = 'stack'
    options = Options(
        Argument('code', required=True),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, code, varname):
        # TODO: language override (the reason this is not implemented, is that language selection is buried way
        #       down somewhere in some method called in render_plugins. There it gets extracted from the request
        #       and a language in request.GET always overrides everything.)
        if not code:
            # an empty string was passed in or the variable is not available in the context
            return ''
        # TODO: caching?
        if isinstance(code, Stack):
            stack = code
        else:
            stack, __ = stack_models.Stack.objects.get_or_create(code=code, defaults={'name': code})
        # TODO: once we drop 2.3.x support we can just use the "render_plugin" templatetag
        #       instead of rendering html here.
        placeholder = stack.content
        plugins = get_plugins(context['request'], placeholder)
        processors = ()
        rendered_placeholder = mark_safe("".join(render_plugins(plugins, context, placeholder, processors)))
        if varname:
            context[varname] = rendered_placeholder
            rendered_placeholder = u''
        return rendered_placeholder

register.tag(StackNode)
