import warnings
from collections import defaultdict
from contextlib import contextmanager
from functools import lru_cache, wraps
from threading import local

from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q

from cms.constants import ROOT_USER_LEVEL, SCRIPT_USERNAME
from cms.exceptions import NoPermissionsException
from cms.models import GlobalPagePermission, PagePermission
from cms.utils.compat.dj import available_attrs
from cms.utils.conf import get_cms_setting
from cms.utils.page import get_clean_username

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


def get_current_user_name():
    current_user = get_current_user()

    if not current_user:
        return SCRIPT_USERNAME
    return get_clean_username(current_user)


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


def user_can_view_placeholder_source(user, source):
    """Whether ``user`` may view the placeholders attached to ``source``.

    Viewing the (read-only) structure board of a frontend-editable object
    requires only *view* permission; mutating its plugins stays gated by
    change permission at the plugin endpoints. This lets headless reviewers
    inspect content structure without edit rights.

    Honours a custom ``has_placeholder_view_permission`` hook on the object
    and otherwise grants access to users holding the model/object ``view`` or
    ``change`` permission (change implies the right to view).
    """
    if hasattr(source, "has_placeholder_view_permission"):
        return source.has_placeholder_view_permission(user)
    model = type(source)
    perms = (
        get_model_permission_codename(model, "view"),
        get_model_permission_codename(model, "change"),
    )
    return any(user.has_perm(perm) or user.has_perm(perm, source) for perm in perms)


def _has_global_permission(user, site, action):
    if not user.is_authenticated:
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


def _global_permission_flags(queryset):
    """OR together the ``can_*`` flags of every row in ``queryset``."""
    flags = GlobalPagePermission.get_all_permissions()
    granted = set()

    for row in queryset.values(*flags):
        granted.update(flag for flag in flags if row[flag])
    return granted


def _managed_global_permission_flags(queryset):
    """Like :func:`_global_permission_flags`, but empty without ``can_change_permissions``.

    Holding a flag on a site is not enough to hand it out there: the user must
    also be allowed to manage permissions on that site.
    """
    granted = _global_permission_flags(queryset)
    return granted if "can_change_permissions" in granted else set()


def get_grantable_global_permissions(user, site_ids=None):
    """Return the ``can_*`` flags ``user`` may hand out through a global permission.

    A delegated permission manager must never grant a right they do not hold
    themselves (see ``docs/explanation/permissions.rst``), so what is grantable
    depends on the sites the grant would cover:

    * ``site_ids=None`` -- the union of the flags the user holds on any site.
      The widest set they could ever grant, used to decide which fields to
      offer at all.
    * ``site_ids=[]`` -- an empty ``GlobalPagePermission.sites`` means "every
      site", so granting requires an equally unrestricted grant of the flag.
    * a non-empty list -- the flags held on *every* one of those sites. A flag
      held on one site alone cannot be used to grant it on another.

    For ``[]`` and a list of sites, nothing is grantable on a site where the user
    lacks ``can_change_permissions``, so ``"can_change_permissions" in result``
    tells whether the user may manage permissions on all of those sites.

    In every case a flag is only grantable if the user also holds the Django
    model permissions that page actions require alongside it.
    """
    all_flags = set(GlobalPagePermission.get_all_permissions())

    if not user or not user.is_authenticated:
        return set()

    if user.is_superuser or not get_cms_setting('PERMISSION'):
        return all_flags

    if site_ids is None:
        held = _global_permission_flags(GlobalPagePermission.objects.with_user(user))
    elif not site_ids:
        held = _managed_global_permission_flags(
            GlobalPagePermission.objects.with_user(user).filter(sites__isnull=True)
        )
    else:
        held = all_flags
        for site_id in site_ids:
            held &= _managed_global_permission_flags(
                GlobalPagePermission.objects.get_with_site(user, site_id)
            )
            if not held:
                break
    return held & _flags_with_django_permissions(user)


# ``can_view`` has no Django permission counterpart: viewing restricted pages
# is governed by CMS permissions alone.
_global_permission_actions = {
    "can_add": "add_page",
    "can_change": "change_page",
    "can_delete": "delete_page",
    "can_publish": "publish_page",
    "can_change_advanced_settings": "change_page_advanced_settings",
    "can_change_permissions": "change_page_permissions",
    "can_move_page": "move_page",
}


def _flags_with_django_permissions(user):
    """Return the ``can_*`` flags whose Django model permissions ``user`` holds.

    A CMS flag alone does not let a user act: the page permission checks also
    require the corresponding Django permissions (``auth_permission_required``).
    A manager holding the flag but not the Django permission does not have the
    right, so they must not be able to hand it out either.
    """
    from cms.utils.page_permissions import _django_permissions_by_action

    return {
        flag for flag in GlobalPagePermission.get_all_permissions()
        if flag not in _global_permission_actions
        or user.has_perms(_django_permissions_by_action[_global_permission_actions[flag]])
    }


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
    if not user.is_authenticated:
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
            .select_related('page')
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


def clear_func_cache(user, func):
    func_cache_name = '_djangocms_cached_func_%s' % func.__name__
    if hasattr(user, func_cache_name):
        delattr(user, func_cache_name)


def clear_permission_lru_caches(user):
    """
    Clear all python lru caches used by the permission system
    """
    clear_func_cache(user, get_global_actions_for_user)
    clear_func_cache(user, get_page_actions_for_user)


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
    actions = defaultdict(list)

    page_permissions = (
        PagePermission
        .objects
        .with_user(user)
        .select_related('page')
        .filter(page__site=site)
    )

    for perm in page_permissions.iterator():
        permission_tuple = perm.grant_on, perm.page.path
        for action in perm.get_configured_actions():
            actions[action].append(permission_tuple)
    return actions


def has_global_permission(user, site, action, use_cache=True):
    if use_cache:
        actions = get_global_actions_for_user(user, site)
    else:
        actions = get_global_actions_for_user.without_cache(user, site)
    return action in actions


def has_page_permission(user, page, action, use_cache=True):
    import warnings

    from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning
    from cms.utils.page_permissions import has_generic_permission

    warnings.warn("has_page_permission is deprecated. "
                  "Use cms.utils.page_permissions.has_generic_permission instead.",
                  RemovedInDjangoCMS51Warning, stacklevel=2)

    action_map = {
        "change": "change_page",
        "add": "add_page",
        "move": "move_page",
        "publish": "publish_page",
        "delete": "delete_page",
        "view": "view_page",
    }
    if action in action_map:
        action = action_map[action]

    return has_generic_permission(page, user, action, site=page.site, check_global=False, use_cache=use_cache)


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

    Superusers are never subordinate to a non-superuser, no matter how many
    permissions the latter holds. Otherwise a delegated administrator could
    manage - and take over - a superuser account.

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
    from cms.utils.page_permissions import get_change_permissions_perm_tuples

    def without_superusers(qs):
        # A non-superuser must never be handed a superuser as a subordinate:
        # being able to manage the account means being able to take it over.
        if user.is_superuser:
            return qs
        return qs.exclude(is_superuser=True)

    try:
        user_level = get_user_permission_level(user, site)
    except NoPermissionsException:
        # user has no Global or Page permissions.
        # return only staff users created by user
        # whose page permission record has no page attached.
        qs = get_user_model().objects.distinct().filter(
            Q(is_staff=True) & Q(pageuser__created_by=user) & Q(pagepermission__page=None)
        )
        qs = qs.exclude(pk=user.pk).exclude(groups__user__pk=user.pk)
        return without_superusers(qs)

    if user_level == ROOT_USER_LEVEL:
        return without_superusers(get_user_model().objects.all())

    from cms.models import PermissionTuple
    allow_list = Q()
    for perm_tuple in get_change_permissions_perm_tuples(user, site, check_global=False):
        allow_list |= PermissionTuple(perm_tuple).allow_list("pagepermission__page")

    # normal query
    qs = get_user_model().objects.distinct().filter(
        Q(is_staff=True) & (
            allow_list & Q(pagepermission__page__depth__gte=user_level)
        ) | (
            Q(pageuser__created_by=user) & Q(pagepermission__page=None)
        )
    )
    qs = qs.exclude(pk=user.pk).exclude(groups__user__pk=user.pk)
    return without_superusers(qs)


def get_subordinate_groups(user, site):
    """
    Similar to get_subordinate_users, but returns queryset of Groups instead
    of Users.
    """
    from cms.utils.page_permissions import get_change_permissions_perm_tuples

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
                Q(pageusergroup__created_by=user) & Q(pagepermission__page__isnull=True)
            )
            .distinct()
        )
        # no permission no records
        # page_id_allow_list is empty
        return groups

    if user_level == ROOT_USER_LEVEL:
        return Group.objects.all()

    from cms.models import PermissionTuple
    allow_list = Q()
    for perm_tuple in get_change_permissions_perm_tuples(user, site, check_global=False):
        allow_list |= PermissionTuple(perm_tuple).allow_list("pagepermission__page")

    return Group.objects.distinct().filter(
        (
            allow_list & Q(pagepermission__page__depth__gte=user_level)
        ) | (
            Q(pageusergroup__created_by=user) & Q(pagepermission__page__isnull=True)
        )
    )


def get_view_restrictions(pages):
    """
    Load all view restrictions for the pages
    """

    from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning

    warnings.warn("get_view_restrictions will be removed",
                  RemovedInDjangoCMS51Warning, stacklevel=2)

    restricted_pages = defaultdict(list)

    if not get_cms_setting('PERMISSION'):
        # Permissions are off. There's no concept of page restrictions.
        return restricted_pages

    if not pages:
        return restricted_pages

    pages_by_id = {}
    for page in pages:
        if page.is_root():
            page._set_hierarchy(pages)
        pages_by_id[page.pk] = page

    page_permissions = PagePermission.objects.filter(
        page__in=pages_by_id,
        can_view=True,
    )

    for perm in page_permissions:
        # set internal fk cache to our page with loaded ancestors and descendants
        PagePermission.page.field.set_cached_value(perm, pages_by_id[perm.page_id])

        for page_id in perm._get_page_ids():
            restricted_pages[page_id].append(perm)
    return restricted_pages


def has_plugin_permission(user, plugin_type, permission_type):
    """
    Checks that a user has permissions for the plugin-type given to perform
    the action defined in permission_type
    permission_type should be 'add', 'change' or 'delete'.
    """
    from cms.plugin_pool import plugin_pool
    try:
        plugin_class = plugin_pool.get_plugin(plugin_type)
        codename = get_model_permission_codename(
            plugin_class.model,
            action=permission_type,
        )
        return user.has_perm(codename)
    except KeyError:
        # Grant all permissions for uninstalled plugins, so they do not block
        # emptying placeholders.
        return True
