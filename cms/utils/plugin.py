from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils import get_language_from_request
from cms import settings
import copy

def render_plugins_for_context(placeholder_name, page, context_to_copy, theme=None):
    """
    renders plugins for the given named placedholder and page using shallow copies of the 
    given context
    """
    context = copy.copy(context_to_copy) 
    l = get_language_from_request(context['request'])
    request = context['request']
    plugins = get_cmsplugin_queryset(request).filter(page=page, language=l, placeholder__iexact=placeholder_name, parent__isnull=True).order_by('position').select_related()
    if settings.CMS_PLACEHOLDER_CONF and placeholder_name in settings.CMS_PLACEHOLDER_CONF:
        if "extra_context" in settings.CMS_PLACEHOLDER_CONF[placeholder_name]:
            context.update(settings.CMS_PLACEHOLDER_CONF[placeholder_name]["extra_context"])
    if theme:
        # this may overwrite previously defined key [theme] from settings.CMS_PLACEHOLDER_CONF
        context.update({'theme': theme,})
    c = ""
    for plugin in plugins:
        c += plugin.render_plugin(copy.copy(context), placeholder_name)
    return c
