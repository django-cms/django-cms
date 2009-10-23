
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
                    })
    output = temp.render(context)
    request.user = user
    placeholders = re.findall("<!-- PlaceholderNode: (.+?) -->", output)
    request.current_page = old_page
    return placeholders

def get_placeholder_plugins(placeholder):
    pass


"""
        edit = False
        if ("edit" in request.GET or request.session.get("cms_edit", False)) and 'cms.middleware.toolbar.ToolbarMiddleware' in django_settings.MIDDLEWARE_CLASSES and request.user.is_staff and request.user.is_authenticated:
            edit = True
        
        if edit:
            installed_plugins = plugin_pool.get_all_plugins(self.name)
            name = self.name
            if settings.CMS_PLACEHOLDER_CONF and self.name in settings.CMS_PLACEHOLDER_CONF:
                if "name" in settings.CMS_PLACEHOLDER_CONF[self.name]:
                    name = settings.CMS_PLACEHOLDER_CONF[self.name]['name']
            name = title(name)
            c += render_to_string("cms/toolbar/add_plugins.html", {'installed_plugins':installed_plugins,
                                                                   'language':request.LANGUAGE_CODE,
                                                                   'placeholder_name':name,
                             
"""