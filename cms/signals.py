# -*- coding: utf-8 -*-
from cms.exceptions import NoHomeFound
from cms.utils.conf import get_cms_setting
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import signals
from django.dispatch import Signal

from cms.cache.permissions import clear_user_permission_cache, clear_permission_cache
from cms.models import Page, Title, CMSPlugin, PagePermission, GlobalPagePermission, PageUser, PageUserGroup, PlaceholderReference, Placeholder
from django.conf import settings
from menus.menu_pool import menu_pool

# fired after page location is changed - is moved from one node to other
page_moved = Signal(providing_args=["instance"])

# fired when some of nodes (Page) with applications gets saved
application_post_changed = Signal(providing_args=["instance"])

# fired after page gets published - copied to public model - there may be more
# than one instances published before this signal gets called
post_publish = Signal(providing_args=["instance", "language"])
post_unpublish = Signal(providing_args=["instance", "language"])


urls_need_reloading = Signal(providing_args=[])
        

signals.post_delete.connect(update_plugin_positions, sender=CMSPlugin, dispatch_uid="cms.plugin.update_position")


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
            home_pk = qs.filter(title_set__published=True).distinct().get_home(instance.site).pk
        except NoHomeFound:
            if instance.publisher_is_draft and instance.title_set.filter(published=True, publisher_public__published=True).count():
                return
            home_pk = instance.pk
            #instance.is_home = True
        for page in qs.filter(site=instance.site, is_home=True).exclude(pk=home_pk):
            if instance.pk == page.pk:
                instance.is_home = False
            page.is_home = False
            page._publisher_keep_state = True
            page._home_checked = True
            page.save()
        try:
            page = qs.get(pk=home_pk, site=instance.site)
        except Page.DoesNotExist:
            return
        page.is_home = True
        if instance.pk == home_pk:
            instance.is_home = True
        page._publisher_keep_state = True
        page._home_checked = True
        page.save()


page_moved.connect(update_home, sender=Page, dispatch_uid="cms.page.update_home")
signals.post_delete.connect(update_home, sender=Page)



page_moved.connect(update_title_paths, sender=Page, dispatch_uid="cms.title.update_path")


signals.pre_save.connect(pre_save_title, sender=Title, dispatch_uid="cms.title.presave")



signals.post_save.connect(post_save_title, sender=Title, dispatch_uid="cms.title.postsave")



if get_cms_setting('PERMISSION'):
    # only if permissions are in use
    from django.contrib.auth.models import User, Group
    # register signals to user related models
    signals.post_save.connect(post_save_user, User)
    signals.post_save.connect(post_save_user_group, Group)




# tell moderator, there is something happening with this page
signals.pre_save.connect(pre_save_page, sender=Page, dispatch_uid="cms.page.presave")
signals.post_save.connect(post_save_page_moderator, sender=Page, dispatch_uid="cms.page.postsave")
signals.post_save.connect(post_save_page, sender=Page)
signals.post_save.connect(update_placeholders, sender=Page)
signals.pre_save.connect(invalidate_menu_cache, sender=Page)
signals.pre_delete.connect(invalidate_menu_cache, sender=Page)
signals.pre_delete.connect(delete_placeholders, sender=Page)
signals.pre_delete.connect(pre_delete_title, sender=Title)


def clear_placeholder_ref(instance, **kwargs):
    instance.placeholder_ref_id_later = instance.placeholder_ref_id


signals.pre_delete.connect(clear_placeholder_ref, sender=PlaceholderReference)


def clear_placeholder_ref_placeholder(instance, **kwargs):
    Placeholder.objects.filter(pk=instance.placeholder_ref_id_later).delete()


signals.post_delete.connect(clear_placeholder_ref_placeholder, sender=PlaceholderReference)


if get_cms_setting('PERMISSION'):
    signals.pre_save.connect(pre_save_user, sender=User)
    signals.pre_delete.connect(pre_delete_user, sender=User)

    signals.pre_save.connect(pre_save_user, sender=PageUser)
    signals.pre_delete.connect(pre_delete_user, sender=PageUser)

    signals.pre_save.connect(pre_save_group, sender=Group)
    signals.pre_delete.connect(pre_delete_group, sender=Group)

    signals.pre_save.connect(pre_save_group, sender=PageUserGroup)
    signals.pre_delete.connect(pre_delete_group, sender=PageUserGroup)

    signals.pre_save.connect(pre_save_pagepermission, sender=PagePermission)
    signals.pre_delete.connect(pre_delete_pagepermission, sender=PagePermission)

    signals.pre_save.connect(pre_save_globalpagepermission, sender=GlobalPagePermission)
    signals.pre_delete.connect(pre_delete_globalpagepermission, sender=GlobalPagePermission)

    signals.pre_save.connect(pre_save_delete_page, sender=Page)
    signals.pre_delete.connect(pre_save_delete_page, sender=Page)



signals.pre_save.connect(apphook_pre_checker, sender=Title)
signals.post_save.connect(apphook_post_checker, sender=Title)
signals.post_delete.connect(apphook_post_delete_checker, sender=Title)

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.models import post_revision_commit

    post_revision_commit.connect(post_revision)
