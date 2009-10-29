import operator

def get_plugins(request, obj):
    if not hasattr(obj, '_plugins_cache'):
        from cms.utils.moderator import get_cmsplugin_queryset
        from cms.utils import get_language_from_request
        l = get_language_from_request(request)
        obj._plugins_cache = get_cmsplugin_queryset(request).filter(page=obj, language=l, parent__isnull=True).order_by('placeholder', 'position').select_related()
    return obj._plugins_cache

def get_plugin_media(request, plugin):
    instance, plugin = plugin.get_plugin_instance()
    return plugin.get_plugin_media(request, instance)

def get_plugins_media(request, obj):
    if not hasattr(obj, '_plugins_media_cache'):
        plugins = get_plugins(request, obj)
        obj._plugins_media_cache = reduce(operator.add, [get_plugin_media(request, plugin) for plugin in plugins])
    return obj._plugins_media_cache