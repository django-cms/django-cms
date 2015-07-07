# -*- coding: utf-8 -*-
from cms.cache.placeholder import clear_placeholder_cache
from cms.constants import PUBLISHER_STATE_DIRTY
from cms.models import CMSPlugin, Title, Page, StaticPlaceholder, Placeholder


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

        if delete_cache:
            clear_placeholder_cache(placeholder, language)

        attached_model = placeholder._get_attached_model()

        if attached_model is Page:
            Title.objects.filter(page=placeholder.page, language=language).update(publisher_state=PUBLISHER_STATE_DIRTY)

        elif attached_model is StaticPlaceholder:
            StaticPlaceholder.objects.filter(draft=placeholder).update(dirty=True)


def pre_save_plugins(**kwargs):
    plugin = kwargs['instance']
    if hasattr(plugin, '_no_reorder'):
        return

    set_dirty(plugin)

    if plugin.pk:
        try:
            old_plugin = CMSPlugin.objects.get(pk=plugin.pk)
        except CMSPlugin.DoesNotExist:
            pass
        else:
            if old_plugin.placeholder_id != plugin.placeholder_id:
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
