# -*- coding: utf-8 -*-
from cms.cache.permissions import clear_permission_cache
from cms.signals.apphook import apphook_post_delete_page_checker
from cms.signals.title import update_title_paths
from menus.menu_pool import menu_pool


def pre_save_page(instance, **kwargs):
    menu_pool.clear(instance.site_id)
    clear_permission_cache()


def pre_delete_page(instance, **kwargs):
    menu_pool.clear(instance.site_id)

    for placeholder in instance.get_placeholders():
        for plugin in placeholder.get_plugins().order_by('-depth'):
            plugin._no_reorder = True
            plugin.delete(no_mp=True)
        placeholder.delete()
    clear_permission_cache()


def post_delete_page(instance, **kwargs):
    apphook_post_delete_page_checker(instance)
    instance.clear_cache()


def post_moved_page(instance, **kwargs):
    update_title_paths(instance, **kwargs)
