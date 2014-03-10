# -*- coding: utf-8 -*-
from cms.constants import PUBLISHER_STATE_DIRTY
from cms.models import CMSPlugin, Title, Page, StaticPlaceholder, Placeholder


def pre_save_plugins(**kwargs):
    from django.core.cache import cache
    plugin = kwargs['instance']
    if hasattr(plugin, '_no_reorder'):
        return
    placeholder = None
    if plugin.placeholder:
        try:
            placeholder = plugin.placeholder
        except Placeholder.DoesNotExist:
            pass
    elif plugin.placeholder_id:
        placeholder = Placeholder.objects.get(pk=plugin.placeholder_id)
    if placeholder:
        cache.delete(placeholder.get_cache_key(plugin.language))
        attached_model = placeholder._get_attached_model()
        if attached_model == Page:
            Title.objects.filter(page=plugin.placeholder.page, language=plugin.language).update(
                publisher_state=PUBLISHER_STATE_DIRTY)
        if attached_model == StaticPlaceholder:
            StaticPlaceholder.objects.filter(draft=placeholder).update(dirty=True)
    if plugin.pk:
        try:
            old_plugin = CMSPlugin.objects.get(pk=plugin.pk)
        except CMSPlugin.DoesNotExist:
            return
        if old_plugin.placeholder_id != plugin.placeholder_id:
            attached_model = old_plugin.placeholder._get_attached_model()
            if attached_model == Page:
                Title.objects.filter(page=old_plugin.placeholder.page, language=old_plugin.language).update(
                    publisher_state=PUBLISHER_STATE_DIRTY)
            if attached_model == StaticPlaceholder:
                StaticPlaceholder.objects.filter(draft=old_plugin.placeholder_id).update(dirty=True)


def pre_delete_plugins(**kwargs):

    from django.core.cache import cache
    plugin = kwargs['instance']
    if hasattr(plugin, '_no_reorder'):
        return
    placeholder = None
    if plugin.placeholder_id:
        try:
            placeholder = plugin.placeholder
        except Placeholder.DoesNotExist:
            pass
    if placeholder:
        cache.delete(placeholder.get_cache_key(plugin.language))
        attached_model = placeholder._get_attached_model()
        if attached_model == Page:
            Title.objects.filter(page=plugin.placeholder.page, language=plugin.language).update(
                publisher_state=PUBLISHER_STATE_DIRTY)
        if attached_model == StaticPlaceholder:
            StaticPlaceholder.objects.filter(draft=plugin.placeholder_id).update(dirty=True)


def post_delete_plugins(**kwargs):
    plugin = kwargs['instance']
    if hasattr(plugin, '_no_reorder'):
        return
    plugins = CMSPlugin.objects.filter(language=plugin.language, placeholder=plugin.placeholder_id,
                                       parent=plugin.parent_id).order_by("position")
    last = 0
    for p in plugins:
        if p.position != last:
            p.position = last
            p.save()
        last += 1

