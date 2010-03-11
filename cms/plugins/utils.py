import operator
from django.forms.widgets import Media
from cms.utils import get_language_from_request
from cms.utils.moderator import get_cmsplugin_queryset

def get_plugins(request, obj, lang=None):
    if not obj:
        return []
    lang = lang or get_language_from_request(request)
    if not hasattr(obj, '_%s_plugins_cache' % lang):
        setattr(obj, '_%s_plugins_cache' % lang,  get_cmsplugin_queryset(request).filter(
            page=obj, language=lang, parent__isnull=True
        ).order_by('placeholder', 'position').select_related() )
    return getattr(obj, '_%s_plugins_cache' % lang)

def get_plugin_media(request, plugin):
    instance, plugin = plugin.get_plugin_instance()
    return plugin.get_plugin_media(request, instance)

def get_plugins_media(request, obj):
    lang = get_language_from_request(request)
    if not obj:
        # current page is unknown
        return []
    if not hasattr(obj, '_%s_plugins_media_cache' % lang):
        plugins = get_plugins(request, obj, lang=lang)
        media_classes = [get_plugin_media(request, plugin) for plugin in plugins]
        if media_classes:
            setattr(obj, '_%s_plugins_media_cache' % lang, reduce(operator.add, media_classes))
        else:
            setattr(obj, '_%s_plugins_media_cache' % lang,  Media())
    return getattr(obj, '_%s_plugins_media_cache' % lang)