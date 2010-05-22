import operator
from django.forms.widgets import Media
from cms.utils import get_language_from_request
from cms.utils.moderator import get_cmsplugin_queryset

def get_plugins(request, placeholder, lang=None):
    if not placeholder:
        return []
    lang = lang or get_language_from_request(request)
    if not hasattr(placeholder, '_%s_plugins_cache' % lang):
        setattr(placeholder, '_%s_plugins_cache' % lang, get_cmsplugin_queryset(request).filter(
            placeholder=placeholder, language=lang, parent__isnull=True
        ).order_by('placeholder', 'position').select_related())
    return getattr(placeholder, '_%s_plugins_cache' % lang)

def get_plugin_media(request, context, plugin):
    instance, plugin = plugin.get_plugin_instance()
    return plugin.get_plugin_media(request, context, instance)

def get_plugins_for_page(request, page, lang=None):
    if not page:
        return []
    lang = lang or get_language_from_request(request)
    if not hasattr(page, '_%s_plugins_cache' % lang):
        setattr(page, '_%s_plugins_cache' % lang,  get_cmsplugin_queryset(request).filter(
            placeholder__page=page, language=lang, parent__isnull=True
        ).order_by('placeholder', 'position').select_related())
    return getattr(page, '_%s_plugins_cache' % lang)

def get_plugins_media(request, context, page):
    lang = get_language_from_request(request)
    if not page:
        # current page is unknown
        return []
    if not hasattr(page, '_%s_plugins_media_cache' % lang):
        plugins = get_plugins_for_page(request, page, lang=lang)
        media_classes = [get_plugin_media(request, context, plugin) for plugin in plugins]
        if media_classes:
            setattr(page, '_%s_plugins_media_cache' % lang, reduce(operator.add, media_classes))
        else:
            setattr(page, '_%s_plugins_media_cache' % lang,  Media())
    return getattr(page, '_%s_plugins_media_cache' % lang)
