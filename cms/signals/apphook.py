# -*- coding: utf-8 -*-

import sys
from django.core.management import color_style
from django.core.urlresolvers import clear_url_caches
from django.core.signals import request_finished
from cms.models import Title
from cms.utils.apphook_reload import mark_urlconf_as_changed


DISPATCH_UID = 'cms-restart'


def trigger_server_restart(**kwargs):
    """
    Marks the URLs as stale so that they can be reloaded.
    """
    mark_urlconf_as_changed()


def apphook_pre_title_checker(instance, **kwargs):
    """
    Store the old application_urls and path on the instance
    """
    if instance.publisher_is_draft:
        return
    try:
        instance._old_data = Title.objects.filter(pk=instance.pk).select_related('page')[0]
    except IndexError:
        instance._old_data = None


def apphook_post_page_checker(page):
    old_page = page.old_page
    if (old_page and (
                old_page.application_urls != page.application_urls or old_page.application_namespace != page.application_namespace)) or (
            not old_page and page.application_urls):

        from cms.cache import invalidate_cms_page_cache
        invalidate_cms_page_cache()
        request_finished.connect(trigger_restart, dispatch_uid=DISPATCH_UID)


def apphook_post_title_checker(instance, **kwargs):
    """
    Check if application_urls and path changed on the instance
    """
    if instance.publisher_is_draft:
        return
    old_title = getattr(instance, '_old_data', None)
    if not old_title:
        if instance.page.application_urls:
            request_finished.connect(
                trigger_restart,
                dispatch_uid=DISPATCH_UID
            )
    else:
        old_values = (
            old_title.published,
            old_title.page.application_urls,
            old_title.page.application_namespace,
            old_title.path,
            old_title.slug,
        )
        new_values = (
            instance.published,
            instance.page.application_urls,
            instance.page.application_namespace,
            instance.path,
            instance.slug,
        )
        if old_values != new_values and (old_values[2] or new_values[2]):
            request_finished.connect(trigger_restart, dispatch_uid=DISPATCH_UID)


def apphook_post_delete_title_checker(instance, **kwargs):
    """
    Check if this was an apphook
    """
    from cms.cache import invalidate_cms_page_cache
    invalidate_cms_page_cache()
    if instance.page.application_urls:
        request_finished.connect(trigger_restart, dispatch_uid=DISPATCH_UID)


def apphook_post_delete_page_checker(instance, **kwargs):
    """
    Check if this was an apphook
    """
    if instance.application_urls:
        request_finished.connect(trigger_restart, dispatch_uid=DISPATCH_UID)

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def trigger_restart(**kwargs):
    from cms.signals import urls_need_reloading

    request_finished.disconnect(trigger_restart, dispatch_uid=DISPATCH_UID)
    urls_need_reloading.send(sender=None)


def debug_server_restart(**kwargs):
    from cms.appresolver import clear_app_resolvers
    if 'runserver' in sys.argv or 'server' in sys.argv:
        clear_app_resolvers()
        clear_url_caches()
        import cms.urls
        try:
            reload(cms.urls)
        except NameError: #python3
            from imp import reload
            reload(cms.urls)
    if not 'test' in sys.argv:
        msg = 'Application url changed and urls_need_reloading signal fired. ' \
              'Please reload the urls.py or restart the server.\n'
        styles = color_style()
        msg = styles.NOTICE(msg)
        sys.stderr.write(msg)
