# -*- coding: utf-8 -*-
import warnings

from django.core.exceptions import ObjectDoesNotExist
from django.template import TemplateDoesNotExist

from cms.cache.permissions import clear_permission_cache
from cms.exceptions import NoHomeFound
from cms.models import Page
from cms.signals.apphook import apphook_post_delete_page_checker, apphook_post_page_checker
from cms.signals.title import update_title, update_title_paths
from menus.menu_pool import menu_pool


def pre_save_page(instance, **kwargs):
    instance.old_page = None
    try:
        instance.old_page = Page.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        pass
    menu_pool.clear(instance.site_id)
    clear_permission_cache()


def post_save_page(instance, **kwargs):
    if not kwargs.get('raw'):
        try:
            instance.rescan_placeholders()
        except TemplateDoesNotExist as e:
            warnings.warn('Exception occurred: %s template does not exists' % e)
        update_home(instance)
    if instance.old_page is None or instance.old_page.parent_id != instance.parent_id or instance.is_home != instance.old_page.is_home:
        pages = [instance] + list(instance.get_descendants())
        for page in pages:
            for title in page.title_set.all().select_related('page'):
                update_title(title)
                title._publisher_keep_state = True
                title.save()
    if (instance.old_page is None and instance.application_urls) or (instance.old_page and (
                instance.old_page.application_urls != instance.application_urls or instance.old_page.application_namespace != instance.application_namespace)):
        if instance.publisher_public_id and instance.publisher_is_draft:
            # this was breaking load data
            try:
                public = instance.publisher_public
                public._publisher_keep_state = True
                public.application_urls = instance.application_urls
                public.application_namespace = instance.application_namespace
                public.save()
            except ObjectDoesNotExist:
                pass
        elif not instance.publisher_is_draft:
            apphook_post_page_checker(instance)


def pre_delete_page(instance, **kwargs):
    menu_pool.clear(instance.site_id)
    for placeholder in instance.get_placeholders():
        for plugin in placeholder.get_plugins().order_by('-depth'):
            plugin._no_reorder = True
            plugin.delete(no_mp=True)
        placeholder.delete()
    clear_permission_cache()


def post_delete_page(instance, **kwargs):
    update_home(instance, **kwargs)
    apphook_post_delete_page_checker(instance)
    from cms.cache import invalidate_cms_page_cache
    invalidate_cms_page_cache()


def post_moved_page(instance, **kwargs):
    update_title_paths(instance, **kwargs)
    update_home(instance, **kwargs)


def update_home(instance, **kwargs):
    """
    Updates the is_home flag of page instances after they are saved or moved.

    :param instance: Page instance
    :param kwargs:
    :return:
    """
    if getattr(instance, '_home_checked', False):
        return
    if not instance.parent_id or (getattr(instance, 'old_page', False) and not instance.old_page.parent_id):
        if instance.publisher_is_draft:
            qs = Page.objects.drafts()
        else:
            qs = Page.objects.public()
        try:
            home_pk = qs.filter(title_set__published=True).distinct().get_home(instance.site_id).pk
        except NoHomeFound:
            if instance.publisher_is_draft and instance.title_set.filter(published=True,
                                                                         publisher_public__published=True).exists():
                return
            home_pk = instance.pk
        for page in qs.filter(site=instance.site_id, is_home=True).exclude(pk=home_pk):
            if instance.pk == page.pk:
                instance.is_home = False
            page.is_home = False
            page._publisher_keep_state = True
            page._home_checked = True
            page.save()
        try:
            page = qs.get(pk=home_pk, site=instance.site_id)
        except Page.DoesNotExist:
            return
        page.is_home = True
        if instance.pk == home_pk:
            instance.is_home = True
        page._publisher_keep_state = True
        page._home_checked = True
        page.save()
