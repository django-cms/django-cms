from django.template import loader, TemplateDoesNotExist
from cms.utils import get_template_from_request
from django.template.context import RequestContext
from django.contrib.auth.models import AnonymousUser
import re

def get_placeholders(request, template_name):
    """
    Return a list of PlaceholderNode found in the given template
    """
    try:
        temp = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return []
    user = request.user
    request.user = AnonymousUser()
    context = RequestContext(request)#details(request, no404=True, only_context=True)
    template = get_template_from_request(request)
    request.current_page = "dummy"
    
    context.update({'template':template,
                    'request':request,
                    'display_placeholder_names_only': True,
                    })
    output = temp.render(context)
    request.user = user
    return re.findall("<!-- PlaceholderNode: (.+?) -->", output)
