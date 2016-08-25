# -*- coding: utf-8 -*-
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from threading import local

from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import Q
from django.utils.decorators import available_attrs
from django.utils.lru_cache import lru_cache

from cms.constants import ROOT_USER_LEVEL
from cms.exceptions import NoPermissionsException
from cms.models import (Page, PagePermission, GlobalPagePermission)
from cms.utils.conf import get_cms_setting


# thread local support
_thread_locals = local()


def set_current_user(user):
    """
    Assigns current user from request to thread_locals, used by
    CurrentUserMiddleware.
    """
    _thread_locals.user = user


def get_current_user():
    """
    Returns current user, or None
    """
    return getattr(_thread_locals, 'user', None)


@contextmanager
def current_user(user):
    """
    Changes the current user just within a context.
    """
    old_user = get_current_user()
    set_current_user(user)
    yield
    set_current_user(old_user)


def get_model_permission_codename(model, action):
    opts = model._meta
    return opts.app_label + '.' + get_permission_codename(action, opts)


def _has_global_permission(user, site, action):
    if not user.is_authenticated():
        return False

    if user.is_superuser:
        return True

    codename = get_model_permission_codename(GlobalPagePermission, action=action)

    if not user.has_perm(codename):
        return False

    if not get_cms_setting('PERMISSION'):
        return True

    has_perm = (
        GlobalPagePermission
        .objects
        .get_with_change_permissions(user, site.pk)
        .exists()
    )
    return has_perm


def user_can_add_global_permissions(user, site):
    return _has_global_permission(user, site, action='add')


def user_can_change_global_permissions(user, site):
    return _has_global_permission(user, site, action='change')


def user_can_delete_global_permissions(user, site):
    return _has_global_permission(user, site, action='delete')


def get_user_permission_level(user, site):
    """
    Returns highest user level from the page/permission hierarchy on which
    user haves can_change_permission. Also takes look into user groups. Higher
    level equals to lower number. Users on top of hierarchy have level 0. Level
    is the same like page.depth attribute.

    Example:
                              A,W                    level 0
                            /    \
                          user    B,GroupE           level 1
                        /     \
                      C,X     D,Y,W                  level 2

        Users A, W have user level 0. GroupE and all his users have user level 1
        If user D is a member of GroupE, his user level will be 1, otherwise is
        2.

    """
    if not user.is_authenticated():
        raise NoPermissionsException

    if user.is_superuser or not get_cms_setting('PERMISSION'):
        return ROOT_USER_LEVEL

    has_global_perms = (
        GlobalPagePermission
        .objects
        .get_with_change_permissions(user, site.pk)
        .exists()
    )

    if has_global_perms:
        return ROOT_USER_LEVEL

    try:
        permission = (
            PagePermission
            .objects
            .get_with_change_permissions(user, site)
            .order_by('page__path')
        )[0]
    except IndexError:
        # user isn't assigned to any node
        raise NoPermissionsException
    return permission.page.depth


def cached_func(func):
    @wraps(func, assigned=available_attrs(func))
    def cached_func(user, *args, **kwargs):
        func_cache_name = '_djangocms_cached_func_%s' % func.__name__

        if not hasattr(user, func_cache_name):
            cached_func = lru_cache(maxsize=None)(func)
            setattr(user, func_cache_name, cached_func)
        return getattr(user, func_cache_name)(user, *args, **kwargs)

    # Allows us to access the un-cached function
    cached_func.without_cache = func
    return cached_func


@cached_func
def get_global_actions_for_user(user, site):
    actions = set()
    global_perms = (
        GlobalPagePermission
        .objects
        .get_with_site(user, site.pk)
    )

    for global_perm in global_perms.iterator():
        actions.update(global_perm.get_configured_actions())
    return actions


@cached_func
def get_page_actions_for_user(user, site):
    actions = defaultdict(set)
    page_permissions = (
        PagePermission
        .objects
        .get_with_site(user, site_id=site.pk)
        .order_by('page__path')
        .select_related('page')
    )

    for permission in page_permissions.iterator():
        page_ids = frozenset(permission.get_page_ids())

        for action in permission.get_configured_actions():
            actions[action].update(page_ids)
    return actions


def has_global_permission(user, site, action, use_cache=True):
    if use_cache:
        actions = get_global_actions_for_user(user, site)
    else:
        actions = get_global_actions_for_user.without_cache(user, site)
    return action in actions


def has_page_permission(user, page, action, use_cache=True):
    if use_cache:
        actions = get_page_actions_for_user(user, page.site)
    else:
        actions = get_page_actions_for_user.without_cache(user, page.site)
    return page.pk in actions[action]


def get_subordinate_users(user, site):
    """
    Returns users queryset, containing all subordinate users to given user
    including users created by given user and not assigned to any page.

    Not assigned users must be returned, because they shouldn't get lost, and
    user should still have possibility to see them.

    Only users created_by given user which are on the same, or lover level are
    returned.

    If user haves global permissions or is a superuser, then he can see all the
    users.

    This function is currently used in PagePermissionInlineAdminForm for limit
    users in permission combobox.

    Example:
                              A,W                    level 0
                            /    \
                          user    B,GroupE           level 1
                Z       /     \
                      C,X     D,Y,W                  level 2

        Rules: W was created by user, Z was created by user, but is not assigned
        to any page.

        Will return [user, C, X, D, Y, Z]. W was created by user, but is also
        assigned to higher level.
    """
    from cms.utils.page_permissions import get_change_permissions_id_list

    try:
        user_level = get_user_permission_level(user, site)
    except NoPermissionsException:
        # user has no Global or Page permissions.
        # return only staff users created by user
        # whose page permission record has no page attached.
        qs = get_user_model().objects.distinct().filter(
                Q(is_staff=True) &
                Q(pageuser__created_by=user) &
                Q(pagepermission__page=None)
        )
        qs = qs.exclude(pk=user.pk).exclude(groups__user__pk=user.pk)
        return qs

    if user_level == ROOT_USER_LEVEL:
        return get_user_model().objects.all()

    page_id_allow_list = get_change_permissions_id_list(user, site, check_global=False)

    # normal query
    qs = get_user_model().objects.distinct().filter(
        Q(is_staff=True) &
        (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__depth__gte=user_level))
        | (Q(pageuser__created_by=user) & Q(pagepermission__page=None))
    )
    qs = qs.exclude(pk=user.pk).exclude(groups__user__pk=user.pk)
    return qs


def get_subordinate_groups(user, site):
    """
    Similar to get_subordinate_users, but returns queryset of Groups instead
    of Users.
    """
    from cms.utils.page_permissions import get_change_permissions_id_list

    try:
        user_level = get_user_permission_level(user, site)
    except NoPermissionsException:
        # user has no Global or Page permissions.
        # return only groups created by user
        # whose page permission record has no page attached.
        groups = (
            Group
            .objects
            .filter(
                Q(pageusergroup__created_by=user) &
                Q(pagepermission__page__isnull=True)
            )
            .distinct()
        )
        # no permission no records
        # page_id_allow_list is empty
        return groups

    if user_level == ROOT_USER_LEVEL:
        return Group.objects.all()

    page_id_allow_list = get_change_permissions_id_list(user, site, check_global=False)

    return Group.objects.distinct().filter(
        (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__depth__gte=user_level))
        | (Q(pageusergroup__created_by=user) & Q(pagepermission__page__isnull=True))
    )


def load_ancestors(pages):
    """
    Loads the ancestors, children and descendants cache for a set of pages.
    :param pages: A queryset of pages to examine
    :return: The list of pages, including ancestors
    """
    pages_by_id = dict((page.pk, page) for page in pages)
    pages_list = list(pages)
    # Ensure that all parent pages are present so that inheritance will work
    # For most use cases, this should not actually do any work
    missing = list(pages)
    while missing:
        page = missing.pop()
        page.ancestors_descending = []
        page._cached_descendants = []
        if page.parent_id and page.parent_id not in pages_by_id:
            pages_list.append(page.parent)
            pages_by_id[page.parent_id] = page.parent
            missing.append(page.parent)
    pages_list.sort(key=lambda page: page.path)
    for page in pages_list:
        if page.parent_id:
            parent = pages_by_id[page.parent_id]
            page.ancestors_descending = parent.ancestors_descending + [parent]
            for ancestor in page.ancestors_descending:
                ancestor._cached_descendants.append(page)
        else:
            page.ancestors_descending = []
        page.ancestors_ascending = list(reversed(page.ancestors_descending))
    return pages_list


def get_view_restrictions(pages):
    """
    Load all view restrictions for the pages
    """
    restricted_pages = defaultdict(list)

    if not get_cms_setting('PERMISSION'):
        # Permissions are off. There's no concept of page restrictions.
        return restricted_pages

    if not pages:
        return restricted_pages

    is_public_pages = not pages[0].publisher_is_draft

    if is_public_pages:
        # Always use draft pages!!!
        draft_ids = (page.publisher_public_id for page in pages)
        pages = Page.objects.filter(pk__in=draft_ids).select_related('parent')

    pages_list = load_ancestors(pages)
    pages_by_id = dict((page.pk, page) for page in pages_list)

    page_permissions = PagePermission.objects.filter(
        page__in=pages_by_id,
        can_view=True,
    )

    for perm in page_permissions:
        # set internal fk cache to our page with loaded ancestors and descendants
        perm._page_cache = pages_by_id[perm.page_id]

        for page_id in perm.get_page_ids():
            restricted_pages[page_id].append(perm)
    return restricted_pages


def get_user_sites_queryset(user):
    """
    Returns queryset of all sites available for given user.

    1.  For superuser always returns all sites.
    2.  For global user returns all sites he haves in global page permissions
        together with any sites he is assigned to over an page.
    3.  For standard user returns just sites he is assigned to over pages.
    """
    qs = Site.objects.all()

    if not get_cms_setting('PERMISSION') or user.is_superuser:
        return qs

    global_ids = GlobalPagePermission.objects.with_user(user).filter(
        Q(can_add=True) | Q(can_change=True)
    ).values_list('id', flat=True)

    query = Q()
    if global_ids:
        query = Q(globalpagepermission__id__in=global_ids)
        # haves some global permissions assigned
        if not qs.filter(query).exists():
            # haves global permissions, but none of sites is specified,
            # so he haves access to all sites
            return qs
    # add some pages if he has permission to add / change them
    query |= (
        Q(Q(djangocms_pages__pagepermission__user=user) |
          Q(djangocms_pages__pagepermission__group__user=user)) &
        Q(Q(djangocms_pages__pagepermission__can_add=True) | Q(djangocms_pages__pagepermission__can_change=True))
    )
    return qs.filter(query).distinct()


def has_plugin_permission(user, plugin_type, permission_type):
    """
    Checks that a user has permissions for the plugin-type given to perform
    the action defined in permission_type
    permission_type should be 'add', 'change' or 'delete'.
    """
    from cms.plugin_pool import plugin_pool
    plugin_class = plugin_pool.get_plugin(plugin_type)
    codename = get_model_permission_codename(
        plugin_class.model,
        action=permission_type,
    )
    return user.has_perm(codename)
