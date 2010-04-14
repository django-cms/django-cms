from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils.placeholder import get_page_from_placeholder_if_exists
from cms.utils import get_language_from_request
from cms.models.pagemodel import Page
from cms import settings
from django.conf import settings as django_settings
from cms.plugin_pool import plugin_pool
from cms.plugins.utils import get_plugins
from django.template.defaultfilters import title
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from cms.plugin_rendering import render_plugins
import copy

def get_page_from_plugin_or_404(cms_plugin):
    return get_object_or_404(Page, placeholders=cms_plugin.placeholder)

def render_plugins_for_context(placeholder, context_to_copy, width=None):
    """
    renders plugins for the given named placedholder and page using shallow copies of the 
    given context
    """
    if width is None:
        width = placeholder.default_width
    context = copy.copy(context_to_copy) 
    l = get_language_from_request(context['request'])
    request = context['request']
    plugins = [plugin for plugin in get_plugins(request, placeholder)]
    page = get_page_from_placeholder_if_exists(placeholder)
    if page:
        template = page.template
    else:
        template = None
    extra_context = settings.CMS_PLACEHOLDER_CONF.get("%s %s" % (template, placeholder.slot), {}).get("extra_context", None)
    if not extra_context:
        extra_context = settings.CMS_PLACEHOLDER_CONF.get(placeholder.slot, {}).get("extra_context", None)
    if extra_context:
        context.update(extra_context)
    if width:
        # this may overwrite previously defined key [width] from settings.CMS_PLACEHOLDER_CONF
        try:
            width = int(width)
            context.update({'width': width,})
        except ValueError:
            pass
    c = []
    edit = False
    if ("edit" in request.GET or request.session.get("cms_edit", False)) and \
            'cms.middleware.toolbar.ToolbarMiddleware' in django_settings.MIDDLEWARE_CLASSES and \
            request.user.is_staff and request.user.is_authenticated() and \
            (not page or page.has_change_permission(request)):
        edit = True
    if edit and settings.PLACEHOLDER_FRONTEND_EDITING:
        installed_plugins = plugin_pool.get_all_plugins(placeholder, page)
        name = settings.CMS_PLACEHOLDER_CONF.get("%s %s" % (template, placeholder.slot), {}).get("name", None)
        if not name:
            name = settings.CMS_PLACEHOLDER_CONF.get(placeholder.slot, {}).get("name", None)
        if not name:
            name = placeholder.slot
        name = title(name)
        c.append(render_to_string("cms/toolbar/add_plugins.html", {'installed_plugins':installed_plugins,
                                                               'language':l,
                                                               'placeholder_label':name,
                                                               'placeholder':placeholder,
                                                               'page':page,
                                                               }))
        from cms.middleware.toolbar import toolbar_plugin_processor
        processors = (toolbar_plugin_processor,)
    else:
        processors = None 
        
    c.extend(render_plugins(plugins, context, placeholder, processors))
    
    return "".join(c)