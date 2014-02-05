# -*- coding: utf-8 -*-
from cms.models import Title


def apphook_pre_checker(instance, **kwargs):
    """
    Store the old application_urls and path on the instance
    """
    try:
        instance._old_data = Title.objects.filter(pk=instance.pk).values_list('application_urls', 'path')[0]
    except IndexError:
        instance._old_data = (None, None)


def apphook_post_checker(instance, **kwargs):
    """
    Check if applciation_urls and path changed on the instance
    """
    from cms.signals import urls_need_reloading
    old_apps, old_path = getattr(instance, '_old_data', (None, None))
    if old_apps != instance.application_urls:
        urls_need_reloading.send(sender=instance)
    elif old_path != instance.path and instance.application_urls:
        urls_need_reloading.send(sender=instance)


def apphook_post_delete_checker(instance, **kwargs):
    """
    Check if this was an apphook
    """
    from cms.signals import urls_need_reloading
    if instance.application_urls:
        urls_need_reloading.send(sender=instance)