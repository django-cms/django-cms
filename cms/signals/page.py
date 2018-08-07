# -*- coding: utf-8 -*-
from cms.cache.permissions import clear_permission_cache
from cms.models.pagemodel import TreeNode
from cms.signals.apphook import set_restart_trigger


def pre_save_page(instance, **kwargs):
    if instance.publisher_is_draft:
        try:
            instance.clear_cache(menu=True)
        except TreeNode.DoesNotExist:
            # can happen while loading fixtures
            pass
        clear_permission_cache()


def pre_delete_page(instance, **kwargs):
    for placeholder in instance.get_placeholders():
        for plugin in placeholder.get_plugins().order_by('-depth'):
            plugin._no_reorder = True
            plugin.delete(no_mp=True)
        placeholder.delete()
    clear_permission_cache()


def post_delete_page(instance, **kwargs):
    if instance.application_urls:
        set_restart_trigger()
