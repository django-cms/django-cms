
from django.template import loader, TemplateDoesNotExist
from cms.utils import get_template_from_request
from django.template.context import RequestContext
from django.contrib.auth.models import AnonymousUser
import re

def get_placeholders(request, template=None):
    """
    Return a list of PlaceholderNode found in the given template
    """
    if not template:
        template = get_template_from_request(request)
    try:
        temp = loader.get_template(template)
    except TemplateDoesNotExist:
        return []
    user = request.user
    request.user = AnonymousUser()
    context = RequestContext(request)#details(request, no404=True, only_context=True)
    template = get_template_from_request(request)
    old_page = request.current_page
    request.current_page = "dummy"
    
    context.update({'template':template,
                    'request':request,
                    'display_placeholder_names_only': True,
                    'current_page': "dummy",
                    })
    output = temp.render(context)
    request.user = user
    placeholders = re.findall("<!-- PlaceholderNode: (.+?) -->", output)
    request.current_page = old_page
    return placeholders

def get_placeholder_plugins(placeholder):
    pass
