from django import template
from django.template import TemplateSyntaxError
from django.template.defaulttags import URLNode
from django.utils.translation import get_language

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
    
    viewname = "%s_%s" % (viewname, get_language())
    return URLNode(viewname, args, kwargs, asvar)
mlurl = register.tag(mlurl)
