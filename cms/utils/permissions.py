# -*- coding: utf-8 -*-
from collections import defaultdict
from contextlib import contextmanager
from threading import local

from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import Q

from cms.exceptions import NoPermissionsException
from cms.models import (Page, PagePermission, GlobalPagePermission,
                        MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS)
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


def user_has_page_add_perm(user, site=None):
    """
    Checks to see if user has add page permission. This is used in multiple
    places so is DRYer as a true function.
    :param user:
    :param site: optional Site object (not just PK)
    :return: Boolean
    """
    if not site:
        site = Site.objects.get_current()

    if get_cms_setting('PERMISSION'):
        global_add_perm = (
            GlobalPagePermission
            .objects
            .user_has_add_permission(user, site.pk)
            .exists()
        )
    else:
        global_add_perm = True
    return has_auth_page_permission(user, action='add') and global_add_perm


def has_page_add_permission(user, target=None, position=None, site=None):
    """
    Return true if the current user has permission to add a new page.
    If we have target and position, check if user can
    add page under target page.
    :param user:
    :param target: a Page object
    :param position: a String "first-child", "last-child", "left", or "right"
    :param site: optional Site object (not just PK)
    :return: Boolean
    """
    if user.is_superuser:
        return True

    if site is None:
        if target:
            site = target.site
        else:
            site = Site.objects.get_current()

    has_add_permission = user_has_page_add_perm(user, site=site)

    if not get_cms_setting('PERMISSION') or not target:
        # If CMS permissions are disabled
        # we can't really check anything but Django permissions.
        # If there's no target then we let the global CMS permission
        # handle user access.
        return has_add_permission

    if has_add_permission:
        # There's a target page
        # and CMS permissions are enabled.
        # User has global add permissions so no need to check
        # the target page.
        return True

    if position in ("first-child", "last-child"):
        return target.has_add_permission(request=None, user=user)
    elif position in ("left", "right"):
        if target.parent_id:
            return has_generic_permission(
                target.parent_id, user, "add", site)
    return False


def has_page_add_permission_from_request(request):
    from cms.utils.helpers import current_site

    if request.user.is_superuser:
        return True

    position = request.GET.get('position', None)
    target_page_id = request.GET.get('target', None)

    if target_page_id:
        try:
            target = Page.objects.get(pk=target_page_id)
        except Page.DoesNotExist:
            return False
    else:
        target = None

    has_add_permission = has_page_add_permission(
        user=request.user,
        target=target,
        position=position,
        site=current_site(request),
    )
    return has_add_permission


def has_any_page_change_permissions(request):
    from cms.utils.helpers import current_site

    if not request.user.is_authenticated():
        return False
    return request.user.is_superuser or PagePermission.objects.filter(
        page__site=current_site(request)
    ).filter(
        Q(user=request.user) |
        Q(group__in=request.user.groups.all())
    ).exists()


def get_model_permission_codename(model, action):
    opts = model._meta
    return opts.app_label + '.' + get_permission_codename(action, opts)


def has_auth_page_permission(user, action):
    """
    Returns True if the user is a superuser or has
    the cms.page {action} permission set via django's permission model.
    """
    if not user.is_superuser:
        permission = get_model_permission_codename(Page, action=action)
        return user.has_perm(permission)
    return True


def has_page_change_permission(request):
    """
    Return true if the current user has permission to change this page.
    To be granted this permission, you need the cms.change_page permission.
    In addition, if CMS_PERMISSION is enabled you also need to either have
    global can_change permission or just on this page.
    """
    from cms.utils.helpers import current_site

    user = request.user
    site = current_site(request)
    global_change_perm = GlobalPagePermission.objects.user_has_change_permission(
        user, site).exists()
    return user.is_superuser or (
        has_auth_page_permission(user, action='change')
        and global_change_perm or has_any_page_change_permissions(request))


def has_global_page_permission(request, site=None, user=None, **filters):
    """
    A helper function to check for global page permissions for the current user
    and site. Caches the result on a request basis, so multiple calls to this
    function inside of one request/response cycle only generate one query.

    :param request: the Request object
    :param site: the Site object or ID
    :param filters: queryset filters, e.g. ``can_add = True``
    :return: ``True`` or ``False``
    """
    if not user:
        user = request.user
    if not user.is_authenticated():
        return False
    if not get_cms_setting('PERMISSION') or user.is_superuser:
        return True
    if not hasattr(request, '_cms_global_perms'):
        request._cms_global_perms = {}
    key = tuple((k, v) for k, v in filters.items())
    if site:
        key = (('site', site.pk if hasattr(site, 'pk') else int(site)),) + key
    if key not in request._cms_global_perms:
        qs = GlobalPagePermission.objects.with_user(user).filter(**filters)
        if site:
            qs = qs.filter(Q(sites__in=[site]) | Q(sites__isnull=True))
        request._cms_global_perms[key] = qs.exists()
    return request._cms_global_perms[key]


def get_user_permission_level(user):
    """
    Returns highest user level from the page/permission hierarchy on which
    user haves can_change_permission. Also takes look into user groups. Higher
    level equals to lover number. Users on top of hierarchy have level 0. Level
    is the same like page.level attribute.

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
    if (user.is_superuser or
            GlobalPagePermission.objects.with_can_change_permissions(user).exists()):
        # those
        return 0
    try:
        permission = PagePermission.objects.with_can_change_permissions(user).order_by('page__path')[0]
    except IndexError:
        # user isn't assigned to any node
        raise NoPermissionsException
    return permission.page.level


def get_subordinate_users(user):
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

    # TODO: try to merge with PagePermissionManager.subordinate_to_user()

    if user.is_superuser or \
            GlobalPagePermission.objects.with_can_change_permissions(user):
        return get_user_model().objects.all()
    site = Site.objects.get_current()
    page_id_allow_list = Page.permissions.get_change_permissions_id_list(user, site)
    try:
        user_level = get_user_permission_level(user)
    except NoPermissionsException:
        # no permission so only staff and no page permissions
        qs = get_user_model().objects.distinct().filter(
                Q(is_staff=True) &
                Q(pageuser__created_by=user) &
                Q(pagepermission__page=None)
        )
        qs = qs.exclude(pk=user.id).exclude(groups__user__pk=user.id)
        return qs
    # normal query
    qs = get_user_model().objects.distinct().filter(
        Q(is_staff=True) &
        (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__level__gte=user_level))
        | (Q(pageuser__created_by=user) & Q(pagepermission__page=None))
    )
    qs = qs.exclude(pk=user.id).exclude(groups__user__pk=user.id)
    return qs


def get_subordinate_groups(user):
    """
    Similar to get_subordinate_users, but returns queryset of Groups instead
    of Users.
    """
    if (user.is_superuser or
            GlobalPagePermission.objects.with_can_change_permissions(user)):
        return Group.objects.all()
    site = Site.objects.get_current()
    page_id_allow_list = Page.permissions.get_change_permissions_id_list(user, site)
    try:
        user_level = get_user_permission_level(user)
    except NoPermissionsException:
        # no permission no records
        # page_id_allow_list is empty
        return Group.objects.distinct().filter(
            Q(pageusergroup__created_by=user) &
            Q(pagepermission__page=None)
        )

    return Group.objects.distinct().filter(
        (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__level__gte=user_level))
        | (Q(pageusergroup__created_by=user) & Q(pagepermission__page=None))
    )


def has_global_change_permissions_permission(request):
    opts = GlobalPagePermission._meta
    user = request.user
    if user.is_superuser or (
        user.has_perm(opts.app_label + '.' + get_permission_codename('change', opts)) and
            has_global_page_permission(request, can_change_permissions=True)):
        return True
    return False


def has_generic_permission(page_id, user, attr, site):
    """
    Permission getter for single page with given id.
    Internally, this calls a method on PagePermissionsPermissionManager
    """
    func = getattr(Page.permissions, "get_%s_id_list" % attr)
    permission = func(user, site)
    return permission == Page.permissions.GRANT_ALL or page_id in permission


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
        page._cached_children = []
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
            parent._cached_children.append(page)
            for ancestor in page.ancestors_descending:
                ancestor._cached_descendants.append(page)
        else:
            page.ancestors_descending = []
        page.ancestors_ascending = list(reversed(page.ancestors_descending))
    return pages_list


def get_any_page_view_permissions(request, page):
    """
    Used by the admin template tag is_restricted
    """
    if not get_cms_setting('PERMISSION'):
        return []  # Maybe None here, to indicate "not applicable"?
    if not hasattr(request, '_cms_view_perms'):
        request._cms_view_perms = {}
    page_id = page.pk if page.publisher_is_draft else page.publisher_public_id
    if page_id not in request._cms_view_perms:
        if not page.publisher_is_draft:
            page = page.publisher_draft
        perms = list(PagePermission.objects.for_page(page=page).filter(can_view=True))
        request._cms_view_perms[page_id] = perms
    return request._cms_view_perms.get(page_id, [])


def load_view_restrictions(request, pages):
    """ Load all view restrictions for the pages and update the cache in the request
    The request cache will receive values for all the pages, but the returned
    dict will only have keys where restrictions actually exist
    """
    restricted_pages = defaultdict(list)
    if get_cms_setting('PERMISSION'):
        if hasattr(request, '_cms_view_perms'):
            cache = request._cms_view_perms
            # TODO: Check if we have anything that requires checking
        else:
            cache = request._cms_view_perms = {}
        pages_list = load_ancestors(pages)
        pages_by_id = {}
        for page in pages_list:
            page_id = page.pk if page.publisher_is_draft else page.publisher_public_id
            pages_by_id[page_id] = page
            cache[page_id] = []
        page_permissions = PagePermission.objects.filter(page__in=pages_by_id, can_view=True).select_related('group__pageusergroup')
        for perm in page_permissions:
            perm_page = pages_by_id[perm.page_id]
            # add the page itself
            if perm.grant_on & MASK_PAGE:
                restricted_pages[perm_page.pk].append(perm)
            # add children
            if perm.grant_on & MASK_CHILDREN:
                children = perm_page.get_children()
                for child in children:
                    restricted_pages[child.pk].append(perm)
            # add descendants
            elif perm.grant_on & MASK_DESCENDANTS:
                descendants = perm_page.get_cached_descendants()
                for child in descendants:
                    restricted_pages[child.pk].append(perm)
        # Overwrite cache where we found restrictions
        cache.update(restricted_pages)

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
    plugin_model = plugin_class.model
    plugin_opts = plugin_model._meta
    return user.has_perm('%s.%s_%s' % (plugin_opts.app_label, permission_type,
                                      plugin_opts.object_name.lower()))
