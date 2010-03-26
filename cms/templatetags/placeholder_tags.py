from django import template
from django.template.defaultfilters import safe

register = template.Library()


class PlaceholderNode(template.Node):
    def __init__(self, placeholder):
        self.placeholder = template.Variable(placeholder)
        
    def render(self, context):
        return safe(self.placeholder.resolve(context).render(context))


def render_placeholder(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tagname, placeholder = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%s takes exactly one argument" % tagname)
    return PlaceholderNode(placeholder)

register.tag('render_placeholder', render_placeholder)