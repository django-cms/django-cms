from django import template
from django.template import TemplateSyntaxError, Node
from django.template.defaulttags import URLNode
from django.utils.translation import get_language
from django.core.urlresolvers import NoReverseMatch
from django.utils.encoding import smart_str
from django.conf import settings

register = template.Library()

def mlurl(parser, token):
    """ Based on django url tag. Just adds language postfix to view name for
    multilinagual stuff.
    """
    bits = token.contents.split(' ')
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    viewname = bits[1]
    args = []
    kwargs = {}
    asvar = None
        
    if len(bits) > 2:
        bits = iter(bits[2:])
        for bit in bits:
            if bit == 'as':
                asvar = bits.next()
                break
            else:
                for arg in bit.split(","):
                    if '=' in arg:
                        k, v = arg.split('=', 1)
                        k = k.strip()
                        kwargs[k] = parser.compile_filter(v)
                    elif arg:
                        args.append(parser.compile_filter(arg))
    
    
    node = MLURLNode(viewname, get_language(), args, kwargs, asvar)
    return node
mlurl = register.tag(mlurl)

class MLURLNode(Node):
    def __init__(self, view_name, language, args, kwargs, asvar):
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar
        self.langauge = language

    def render(self, context):
        from django.core.urlresolvers import reverse, NoReverseMatch
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k,'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        # Try to look up the URL twice: once given the view name, and again
        # relative to what we guess is the "main" app. If they both fail,
        # re-raise the NoReverseMatch unless we're using the
        # {% url ... as var %} construct in which cause return nothing.
        url = ''
        try:
            ml_viewname = "%s_%s" % (self.view_name, get_language())
            url = reverse(ml_viewname, args=args, kwargs=kwargs, current_app=context.current_app)
        except NoReverseMatch, e:
            try:
                url = reverse(self.view_name, args=args, kwargs=kwargs, current_app=context.current_app)
            except NoReverseMatch, e:
                if settings.SETTINGS_MODULE:
                    project_name = settings.SETTINGS_MODULE.split('.')[0]
                    try:
                        url = reverse(project_name + '.' + self.view_name,
                                  args=args, kwargs=kwargs, current_app=context.current_app)
                    except NoReverseMatch:
                        if self.asvar is None:
                            # Re-raise the original exception, not the one with
                            # the path relative to the project. This makes a
                            # better error message.
                            raise e
                else:
                    if self.asvar is None:
                        raise e
        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url
