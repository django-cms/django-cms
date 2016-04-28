# -*- coding: utf-8 -*-
from cms.models import CMSPlugin, Placeholder


def get_placeholder(plugin):
    if plugin.placeholder_id:
        try:
            return plugin.placeholder
        except Placeholder.DoesNotExist:
            return None
    else:
        return plugin.placeholder


def set_dirty(plugin, delete_cache=True):
    placeholder = get_placeholder(plugin)

    if placeholder:
        language = plugin.language

        placeholder.mark_as_dirty(language, clear_cache=delete_cache)


def pre_save_plugins(**kwargs):
    plugin = kwargs['instance']

    if hasattr(plugin, '_no_reorder'):
        return

    set_dirty(plugin)

    if not plugin.pk:
        return

    try:
        old_plugin = (
            CMSPlugin
            .objects
            .select_related('placeholder')
            .only('language', 'placeholder')
            .exclude(placeholder=plugin.placeholder_id)
            .get(pk=plugin.pk)
        )
    except CMSPlugin.DoesNotExist:
        pass
    else:
        set_dirty(old_plugin, delete_cache=False)


def pre_delete_plugins(**kwargs):
    plugin = kwargs['instance']
    if hasattr(plugin, '_no_reorder'):
        return

    set_dirty(plugin)


def post_delete_plugins(**kwargs):
    plugin = kwargs['instance']
    if hasattr(plugin, '_no_reorder'):
        return

    plugins = CMSPlugin.objects.filter(language=plugin.language, placeholder=plugin.placeholder_id,
                                       parent=plugin.parent_id).order_by('position')
    for pos, p in enumerate(plugins):
        if p.position != pos:
            p.position = pos
            p.save()
