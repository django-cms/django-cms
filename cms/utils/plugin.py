from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils import get_language_from_request
from cms import settings
from django.conf import settings as django_settings
from cms.plugin_pool import plugin_pool
from cms.plugins.utils import get_plugins
from django.template.defaultfilters import title
from django.template.loader import render_to_string
import copy

def render_plugins_for_context(placeholder_name, page, context_to_copy, width=None):
    """
    renders plugins for the given named placedholder and page using shallow copies of the 
    given context
    """
    context = copy.copy(context_to_copy) 
    l = get_language_from_request(context['request'])
    request = context['request']
    plugins = [plugin for plugin in get_plugins(request, page) if plugin.placeholder == placeholder_name]
    if settings.CMS_PLACEHOLDER_CONF and placeholder_name in settings.CMS_PLACEHOLDER_CONF:
        if "extra_context" in settings.CMS_PLACEHOLDER_CONF[placeholder_name]:
            context.update(settings.CMS_PLACEHOLDER_CONF[placeholder_name]["extra_context"])
    if width:
        # this may overwrite previously defined key [width] from settings.CMS_PLACEHOLDER_CONF
        try:
            width = int(width)
            context.update({'width': width,})
        except ValueError:
            pass
    c = []
    edit = False
    if ("edit" in request.GET or request.session.get("cms_edit", False)) and 'cms.middleware.toolbar.ToolbarMiddleware' in django_settings.MIDDLEWARE_CLASSES and request.user.is_staff and request.user.is_authenticated:
        edit = True
    if edit:
        installed_plugins = plugin_pool.get_all_plugins(placeholder_name, page)
        name = placeholder_name
        if settings.CMS_PLACEHOLDER_CONF and placeholder_name in settings.CMS_PLACEHOLDER_CONF:
            if "name" in settings.CMS_PLACEHOLDER_CONF[placeholder_name]:
                name = settings.CMS_PLACEHOLDER_CONF[placeholder_name]['name']
        name = title(name)
        c.append(render_to_string("cms/toolbar/add_plugins.html", {'installed_plugins':installed_plugins,
                                                               'language':request.LANGUAGE_CODE,
                                                               'placeholder_label':name,
                                                               'placeholder_name':placeholder_name,
                                                               'page':page,
                                                               }))
    for index, plugin in enumerate(plugins):
        context['plugin_index'] = index
        c.append(plugin.render_plugin(copy.copy(context), placeholder_name, edit=edit))
    return "".join(c)


                             
