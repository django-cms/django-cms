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
        # TODO: language override (the reason this is not implemented, is that language selection is buried way
        #       down somewhere in some method called in render_plugins. There it gets extracted from the request
        #       and a language in request.GET always overrides everything.)
        if not code:
            # an empty string was passed in or the variable is not available in the context
            return ''
            # TODO: caching?
        request = context.get('request', False)
        if not request:
            return ''
        if isinstance(code, Stack):
            stack = code
        else:
            stack, __ = Stack.objects.get_or_create(code=code, defaults={'name': code,
                'creation_method': Stack.CREATION_BY_TEMPLATE})
        toolbar = request.toolbar
        if stack.dirty:
            if not hasattr(request, 'dirty_stacks'):
                request.dirty_stacks = []
            request.dirty_stacks.append(stack)
        if toolbar.edit:
            placeholder = stack.draft
        else:
            placeholder = stack.live
        return render_placeholder(placeholder, context, name_fallback=code)


register.tag(StackNode)
