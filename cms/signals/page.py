# -*- coding: utf-8 -*-
from cms.cache.permissions import clear_permission_cache
from cms.signals.apphook import set_restart_trigger


def pre_save_page(instance, **kwargs):
    if instance.publisher_is_draft and not kwargs.get('raw'):
        instance.clear_cache(menu=True)
        clear_permission_cache()


def pre_delete_page(instance, **kwargs):
    instance.get_placeholders().delete()
    clear_permission_cache()


def post_delete_page(instance, **kwargs):
    if instance.application_urls:
        set_restart_trigger()
