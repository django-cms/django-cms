from django.template import loader, Context, TemplateDoesNotExist
from django.template.loader_tags import ExtendsNode
from cms.utils import get_template_from_request

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
                    })
    # lacks - it requests context in admin and eats user messages,
    # standard context will be hopefully enough here
    
    # temp.render(RequestContext(request, context))
    temp.render(context)
    
    list = []
    placeholders_recursif(temp.nodelist, list)
    return list

def placeholders_recursif(nodelist, list):
    """
    Recursively search into a template node list for PlaceholderNode node
    """
    for node in nodelist:
        if isinstance(node, PlaceholderNode):
            in_list = False
            for l in list:
                if l.name == node.name:
                    in_list = True
                    break
            if not in_list:
                list.append(node)
            node.render(Context({'current_page':None}))
        for key in ('nodelist', 'nodelist_true', 'nodelist_false'):
            if hasattr(node, key):
                try:
                    placeholders_recursif(getattr(node, key), list)
                except:
                    pass
    for node in nodelist:
        if isinstance(node, ExtendsNode):
            placeholders_recursif(node.get_parent(Context()).nodelist, list)
