from django.template import loader, Context, TemplateDoesNotExist
from django.template.loader_tags import ExtendsNode
from cms.utils import get_template_from_request
import re

# must be imported like this for isinstance
from django.templatetags.cms_tags import PlaceholderNode #do not remove

def get_placeholders(request, template_name):
    """
    Return a list of PlaceholderNode found in the given template
    """
    try:
        temp = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return []
    context = Context()#RequestContext(request)#details(request, no404=True, only_context=True)
    template = get_template_from_request(request)
    request.current_page = "dummy"
    context.update({'template':template,
                    'request':request,
                    'display_placeholder_names_only': True,
                    })
    # lacks - it requests context in admin and eats user messages,
    # standard context will be hopefully enough here
    
    # temp.render(RequestContext(request, context))
    output = temp.render(context)
    return re.findall("<!-- PlaceholderNode: (.+?) -->", output)
