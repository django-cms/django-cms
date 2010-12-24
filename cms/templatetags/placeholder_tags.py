from classytags.arguments import Argument
from classytags.core import Tag, Options
from django import template
from django.template.defaultfilters import safe

register = template.Library()


class RenderPlaceholder(Tag):
    name = 'render_placeholder'
    options = Options(
        Argument('placeholder'),
        Argument('width', default=None, required=False),
    )

    def render_tag(self, context, placeholder, width):
        request = context.get('request', None)
        if not request:
            return ''
        if not placeholder:
            return ''
        if hasattr(request, 'placeholder_media'):
            request.placeholder_media += placeholder.get_media(request, context)
        return safe(placeholder.render(context, width))
register.tag(RenderPlaceholder)