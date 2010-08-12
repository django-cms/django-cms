from django import template
from django.template.defaultfilters import safe
from cms.plugins.utils import get_plugin_media

register = template.Library()


class PlaceholderNode(template.Node):
    def __init__(self, placeholder, width):
        self.placeholder = placeholder
        self.width = width
        
    def render(self, context):
        request = context.get('request', None)
        if not request:
            return ''
        if self.width is not None:
            width = self.width.resolve(context)
        else:
            width = self.width
        placeholder = self.placeholder.resolve(context)
        if not placeholder:
            return ''
        if hasattr(request, 'placeholder_media'):
            request.placeholder_media += placeholder.get_media(request, context)
        return safe(placeholder.render(context, width))


def render_placeholder(parser, token):
    bits = token.split_contents()
    if len(bits) not in (2,3):
        raise template.TemplateSyntaxError("%s takes exactly one or two arguments" % bits[0])
    width = None
    if len(bits) == 3:
        width = parser.compile_filter(bits[2])
    name = parser.compile_filter(bits[1])
    return PlaceholderNode(name, width)

register.tag('render_placeholder', render_placeholder)