from django.template import loader, Context, RequestContext, TemplateDoesNotExist
from django.template.loader_tags import ExtendsNode
# must be imported like this for isinstance
from django.templatetags.pages_tags import PlaceholderNode

from cms.views import details

def get_placeholders(request, template_name):
    """
    Return a list of PlaceholderNode found in the given template
    """
    try:
        temp = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return []
    context = details(request, only_context=True)
    
    temp.render(RequestContext(request, context))
    list = []
    placeholders_recursif(temp.nodelist, list)
    return list

def placeholders_recursif(nodelist, list):
    """
    Recursively search into a template node list for PlaceholderNode node
    """
    for node in nodelist:
        if isinstance(node, PlaceholderNode):
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
