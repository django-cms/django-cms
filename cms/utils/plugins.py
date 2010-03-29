#from django.template import loader, TemplateDoesNotExist
#from cms.utils import get_template_from_request
#from django.template.context import RequestContext
#from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from cms.templatetags.cms_tags import PlaceholderNode
from django.template.loader import find_template
from django.template import Lexer,
#import re
        
def get_placeholders(template):
    source, origin = find_template(template)
    lexer = Lexer(source, origin)
    placeholders = []
    for token in [t for t in lexer.tokenize() if t.token_type == 2]:
        bits = token.split_contents()
        if bits[0] == 'placeholder':
            placeholders.append(bits[1].strip('"\''))
    return placeholders


SITE_VAR = "site__exact"

def current_site(request):
    if SITE_VAR in request.REQUEST:
        return Site.objects.get(pk=request.REQUEST[SITE_VAR])
    else:
        site_pk = request.session.get('cms_admin_site', None)
        if site_pk:
            try:
                return Site.objects.get(pk=site_pk)
            except Site.DoesNotExist:
                return None
        else:
            return Site.objects.get_current()