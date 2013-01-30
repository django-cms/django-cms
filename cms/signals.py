# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import signals
from django.dispatch import Signal

from cms.cache.permissions import clear_user_permission_cache, clear_permission_cache
from cms.models import Page, Title, CMSPlugin, PagePermission, GlobalPagePermission, PageUser, PageUserGroup

from menus.menu_pool import menu_pool

# fired after page location is changed - is moved from one node to other
page_moved = Signal(providing_args=["instance"])

# fired when some of nodes (Title) with applications gets saved
application_post_changed = Signal(providing_args=["instance"])

# fired after page gets published - copied to public model - there may be more
# than one instances published before this signal gets called
post_publish = Signal(providing_args=["instance"])


def update_plugin_positions(**kwargs):
    plugin = kwargs['instance']
    plugins = CMSPlugin.objects.filter(language=plugin.language, placeholder=plugin.placeholder).order_by("position")
    last = 0
    for p in plugins:
        if p.position != last:
            p.position = last
            p.save()
        last += 1


signals.post_delete.connect(update_plugin_positions, sender=CMSPlugin, dispatch_uid="cms.plugin.update_position")


def update_title_paths(instance, **kwargs):
    """Update child pages paths in case when page was moved.
    """
    for title in instance.title_set.all():
        title.save()


page_moved.connect(update_title_paths, sender=Page, dispatch_uid="cms.title.update_path")


def update_title(title):
    slug = u'%s' % title.slug

    if title.page.is_home():
        title.path = ''
    elif not title.has_url_overwrite:
        title.path = u'%s' % slug
        parent_page_id = title.page.parent_id

        if parent_page_id:
            parent_title = Title.objects.get_title(parent_page_id,
                                                   language=title.language, language_fallback=True)
            if parent_title:
                title.path = (u'%s/%s' % (parent_title.path, slug)).lstrip("/")


def pre_save_title(instance, raw, **kwargs):
    """Save old state to instance and setup path
    """
    if not instance.page.publisher_is_draft:
        menu_pool.clear(instance.page.site_id)
    if instance.id and not hasattr(instance, "tmp_path"):
        instance.tmp_path = None
        instance.tmp_application_urls = None
        try:
            instance.tmp_path, instance.tmp_application_urls = \
                Title.objects.filter(pk=instance.id).values_list('path', 'application_urls')[0]
        except IndexError:
            pass  # no Titles exist for this page yet

    # Build path from parent page's path and slug
    if instance.has_url_overwrite and instance.path:
        instance.path = instance.path.strip(" /")
    else:
        update_title(instance)


signals.pre_save.connect(pre_save_title, sender=Title, dispatch_uid="cms.title.presave")


def post_save_title(instance, raw, created, **kwargs):
    # Update descendants only if path changed
    application_changed = False
    prevent_descendants = hasattr(instance, 'tmp_prevent_descendant_update')
    if instance.path != getattr(instance, 'tmp_path', None) and not prevent_descendants:
        descendant_titles = Title.objects.filter(
            page__lft__gt=instance.page.lft,
            page__rght__lt=instance.page.rght,
            page__tree_id__exact=instance.page.tree_id,
            language=instance.language,
            has_url_overwrite=False, # TODO: what if child has no url overwrite?
        ).order_by('page__tree_id', 'page__parent', 'page__lft')

        for descendant_title in descendant_titles:
            descendant_title.path = ''  # just reset path
            descendant_title.tmp_prevent_descendant_update = True
            if descendant_title.application_urls:
                application_changed = True
            descendant_title.save()

    if not prevent_descendants and \
            (instance.application_urls != getattr(instance, 'tmp_application_urls', None) or application_changed):
        # fire it if we have some application linked to this page or some descendant
        application_post_changed.send(sender=Title, instance=instance)

    # remove temporary attributes
    if hasattr(instance, 'tmp_path'):
        del instance.tmp_path
    if hasattr(instance, 'tmp_application_urls'):
        del instance.tmp_application_urls
    if prevent_descendants:
        del instance.tmp_prevent_descendant_update


signals.post_save.connect(post_save_title, sender=Title, dispatch_uid="cms.title.postsave")


def post_save_user(instance, raw, created, **kwargs):
    """Signal called when new user is created, required only when CMS_PERMISSION.
    Assigns creator of the user to PageUserInfo model, so we know who had created
    this user account.
    
    requires: CurrentUserMiddleware
    """
    from cms.utils.permissions import get_current_user
    # read current user from thread locals
    creator = get_current_user()
    if not creator or not created or creator.is_anonymous():
        return

    page_user = PageUser(user_ptr_id=instance.pk, created_by=creator)
    page_user.__dict__.update(instance.__dict__)
    page_user.save()


def post_save_user_group(instance, raw, created, **kwargs):
    """The same like post_save_user, but for Group, required only when 
    CMS_PERMISSION.
    Assigns creator of the group to PageUserGroupInfo model, so we know who had
    created this user account.
    
    requires: CurrentUserMiddleware
    """
    from cms.utils.permissions import get_current_user
    # read current user from thread locals
    creator = get_current_user()
    if not creator or not created or creator.is_anonymous():
        return
    page_user = PageUserGroup(group_ptr_id=instance.pk, created_by=creator)
    page_user.__dict__.update(instance.__dict__)
    page_user.save()


if get_cms_setting('PERMISSION'):
    # only if permissions are in use
    from django.contrib.auth.models import User, Group
    # register signals to user related models
    signals.post_save.connect(post_save_user, User)
    signals.post_save.connect(post_save_user_group, Group)


def pre_save_page(instance, raw, **kwargs):
    """Assigns old_page attribute, so we can compare changes.
    """
    instance.old_page = None
    try:
        instance.old_page = Page.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        pass


def post_save_page_moderator(instance, raw, created, **kwargs):
    """Helper post save signal.
    """
    old_page = instance.old_page

    # tell moderator something was happen with this page
    from cms.utils.moderator import page_changed

    if not old_page:
        page_changed(instance, old_page)


def post_save_page(instance, **kwargs):
    if instance.old_page is None or instance.old_page.parent_id != instance.parent_id:
        for page in instance.get_descendants(include_self=True):
            for title in page.title_set.all():
                update_title(title)
                title.save()


def update_placeholders(instance, **kwargs):
    if not kwargs.get('raw'):
        instance.rescan_placeholders()


def invalidate_menu_cache(instance, **kwargs):
    menu_pool.clear(instance.site_id)

# tell moderator, there is something happening with this page
signals.pre_save.connect(pre_save_page, sender=Page, dispatch_uid="cms.page.presave")
signals.post_save.connect(post_save_page_moderator, sender=Page, dispatch_uid="cms.page.postsave")
signals.post_save.connect(post_save_page, sender=Page)
signals.post_save.connect(update_placeholders, sender=Page)
signals.pre_save.connect(invalidate_menu_cache, sender=Page)
signals.pre_delete.connect(invalidate_menu_cache, sender=Page)


def pre_save_user(instance, raw, **kwargs):
    clear_user_permission_cache(instance)


def pre_delete_user(instance, **kwargs):
    clear_user_permission_cache(instance)


def pre_save_group(instance, raw, **kwargs):
    if instance.pk:
        for user in instance.user_set.all():
            clear_user_permission_cache(user)


def pre_delete_group(instance, **kwargs):
    for user in instance.user_set.all():
        clear_user_permission_cache(user)


def _clear_users_permissions(instance):
    if instance.user:
        clear_user_permission_cache(instance.user)
    if instance.group:
        for user in instance.group.user_set.all():
            clear_user_permission_cache(user)


def pre_save_pagepermission(instance, raw, **kwargs):
    _clear_users_permissions(instance)


def pre_delete_pagepermission(instance, **kwargs):
    _clear_users_permissions(instance)


def pre_save_globalpagepermission(instance, raw, **kwargs):
    _clear_users_permissions(instance)
    menu_pool.clear(all=True)


def pre_delete_globalpagepermission(instance, **kwargs):
    _clear_users_permissions(instance)


def pre_save_delete_page(instance, **kwargs):
    clear_permission_cache()


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
