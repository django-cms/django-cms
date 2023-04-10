from django.apps import apps
from django.conf import settings

from cms.cache.permissions import clear_user_permission_cache
from cms.models import PageUser, PageUserGroup
from menus.menu_pool import menu_pool


def post_save_user(instance, raw, created, **kwargs):
    """Signal called when new user is created, required only when CMS_PERMISSION.
    Assigns creator of the user to PageUserInfo model, so we know who had created
    this user account.

    requires: CurrentUserMiddleware
    """
    from cms.utils.permissions import get_current_user

    # read current user from thread locals
    creator = get_current_user()
    if not creator or not created or creator.is_anonymous:
        return
    if settings.AUTH_USER_MODEL:
        # looks for a custom user profile
        auth_model = apps.get_model(settings.AUTH_USER_MODEL)
        # creates a dynamic kwargs dict with a pointer to the right user model
        kwargs = {
            f"{auth_model._meta.model_name}_ptr_id": instance.pk,
            "created_by": creator
        }
        page_user = PageUser(**kwargs)
    else:
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
    if not creator or not created or creator.is_anonymous:
        return
    page_user = PageUserGroup(group_ptr_id=instance.pk, created_by=creator)
    page_user.__dict__.update(instance.__dict__)
    page_user.save()


def pre_save_user(instance, raw, **kwargs):
    clear_user_permission_cache(instance)


def pre_delete_user(instance, **kwargs):
    clear_user_permission_cache(instance)


def pre_save_group(instance, raw, **kwargs):
    if instance.pk:
        user_set = instance.user_set
        for user in user_set.all():
            clear_user_permission_cache(user)


def pre_delete_group(instance, **kwargs):
    user_set = instance.user_set
    for user in user_set.all():
        clear_user_permission_cache(user)


def _clear_users_permissions(instance):
    if instance.user:
        clear_user_permission_cache(instance.user)
    if instance.group:
        user_set = instance.group.user_set
        for user in user_set.all():
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
