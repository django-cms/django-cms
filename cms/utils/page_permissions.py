from functools import wraps

from cms.cache.permissions import get_permission_cache, set_permission_cache
from cms.constants import GRANT_ALL_PERMISSIONS
from cms.models import Page, PermissionTuple
from cms.utils import get_current_site
from cms.utils.compat.dj import available_attrs
from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import (
    cached_func,
    get_model_permission_codename,
    get_page_actions_for_user,
    has_global_permission,
)

PAGE_ADD_CODENAME = get_model_permission_codename(Page, 'add')
PAGE_CHANGE_CODENAME = get_model_permission_codename(Page, 'change')
PAGE_DELETE_CODENAME = get_model_permission_codename(Page, 'delete')
PAGE_PUBLISH_CODENAME = get_model_permission_codename(Page, 'publish')
PAGE_VIEW_CODENAME = get_model_permission_codename(Page, 'view')


# Maps an action to the required Django auth permission codes
_django_permissions_by_action = {
    'add_page': [PAGE_ADD_CODENAME, PAGE_CHANGE_CODENAME],
    'change_page': [PAGE_CHANGE_CODENAME],
    'change_page_advanced_settings': [PAGE_CHANGE_CODENAME],
    'change_page_permissions': [PAGE_CHANGE_CODENAME],
    'delete_page': [PAGE_CHANGE_CODENAME, PAGE_DELETE_CODENAME],
    'delete_page_translation': [PAGE_CHANGE_CODENAME, PAGE_DELETE_CODENAME],
    'move_page': [PAGE_CHANGE_CODENAME],
    'publish_page': [PAGE_CHANGE_CODENAME, PAGE_PUBLISH_CODENAME],
}


def _get_all_placeholders(page, language=None):
    from django.contrib.contenttypes.models import ContentType

    from cms.models import PageContent, Placeholder

    page_contents = PageContent.admin_manager.filter(page=page)
    if language:
        page_contents = page_contents.filter(language=language)
    content_type = ContentType.objects.get_for_model(Placeholder)
    return Placeholder.objects.filter(
        content_type=content_type,
        object_id__in=page_contents.values_list('pk', flat=True)
    )


def _check_delete_translation(user, page, language, site=None):
    return user_can_change_page(user, page, site=site)


def _get_page_permission_tuples_for_action(user, site, action, check_global=True, use_cache=True):
    if user.is_superuser or not get_cms_setting('PERMISSION'):
        # got superuser, or permissions aren't enabled?
        # just return grant all mark
        return GRANT_ALL_PERMISSIONS

    if check_global and has_global_permission(user, site, action=action, use_cache=use_cache):
        return GRANT_ALL_PERMISSIONS

    if use_cache:
        # read from cache if possible
        cached = get_permission_cache(user, action)
        get_page_actions = get_page_actions_for_user
    else:
        cached = None
        get_page_actions = get_page_actions_for_user.without_cache

    if cached is not None:
        return cached

    page_actions = get_page_actions(user, site)
    # Set cache for all actions calculated
    for act, page_paths in page_actions.items():
        set_permission_cache(user, act, list(page_paths))
    return page_actions[action]


def auth_permission_required(action):
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def wrapper(user, *args, **kwargs):
            if not user.is_authenticated:
                return False

            permissions = _django_permissions_by_action[action]

            if not user.has_perms(permissions):
                # Fail fast if the user does not have permissions
                # in Django to perform the action.
                return False

            permissions_enabled = get_cms_setting('PERMISSION')

            if not user.is_superuser and permissions_enabled:
                return func(user, *args, **kwargs)
            return True
        return wrapper
    return decorator


def change_permission_required(func):
    @wraps(func, assigned=available_attrs(func))
    def wrapper(user, page, site=None):
        if not user_can_change_page(user, page, site=site):
            return False
        return func(user, page, site=site)
    return wrapper


def skip_if_permissions_disabled(func):
    @wraps(func, assigned=available_attrs(func))
    def wrapper(user, page, site=None):
        if not get_cms_setting('PERMISSION'):
            return True
        return func(user, page, site=site)
    return wrapper


@cached_func
@auth_permission_required('add_page')
def user_can_add_page(user, site=None):
    if site is None:
        site = get_current_site()
    return has_global_permission(user, site, action='add_page')


@cached_func
@auth_permission_required('add_page')
def user_can_add_subpage(user, target, site=None):
    """
    Return true if the current user has permission to add a new page
    under target.
    :param user:
    :param target: a Page object
    :param site: optional Site object (not just PK)
    :return: Boolean
    """
    has_perm = has_generic_permission(
        page=target,
        user=user,
        action='add_page',
        site=site,
    )
    return has_perm


@cached_func
@auth_permission_required('change_page')
def user_can_change_page(user, page, site=None):
    can_change = has_generic_permission(
        page=page,
        user=user,
        action='change_page',
        site=site,
    )
    return can_change


@cached_func
@auth_permission_required('delete_page')
def user_can_delete_page(user, page, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='delete_page',
        site=site,
    )

    if not has_perm:
        return False

    placeholders = _get_all_placeholders(page)
    for placeholder in placeholders:
        if not placeholder.has_delete_plugins_permission(user, [placeholders.source.language]):
            return False
    return True


@cached_func
@auth_permission_required('delete_page_translation')
def user_can_delete_page_translation(user, page, language, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='delete_page_translation',
        site=site,
    )

    if not has_perm:
        return False

    placeholders = (
        _get_all_placeholders(page, language)
        .filter(cmsplugin__language=language)
        .distinct()
    )

    for placeholder in placeholders.iterator():
        if not placeholder.has_delete_plugins_permission(user, [language]):
            return False
    return True


@cached_func
@auth_permission_required('publish_page')
def user_can_publish_page(user, page, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='publish_page',
        site=site,
    )
    return has_perm


@cached_func
@auth_permission_required('change_page_advanced_settings')
def user_can_change_page_advanced_settings(user, page, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='change_page_advanced_settings',
        site=site,
    )
    return has_perm


@cached_func
@auth_permission_required('change_page_permissions')
def user_can_change_page_permissions(user, page, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='change_page_permissions',
        site=site,
    )
    return has_perm


@cached_func
@auth_permission_required('move_page')
def user_can_move_page(user, page, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='move_page',
        site=site,
    )
    return has_perm


@cached_func
def user_can_view_page(user, page, site=None):
    if site is None:
        site = get_current_site()

    if user.is_superuser:
        return True

    public_for = get_cms_setting('PUBLIC_FOR')
    can_see_unrestricted = public_for == 'all' or (public_for == 'staff' and user.is_staff)

    # inherited and direct view permissions
    is_restricted = page.has_view_restrictions(site)

    if not is_restricted and can_see_unrestricted:
        # Page has no restrictions and project is configured
        # to allow everyone to see unrestricted pages.
        return True
    elif not user.is_authenticated:
        # Page has restrictions or project is configured
        # to require staff user status to see pages.
        return False

    if user_can_view_all_pages(user, site=site):
        return True

    if not is_restricted:
        # Page has no restrictions but user can't see unrestricted pages
        return False

    if user_can_change_page(user, page):
        # If user has change permissions on a page
        # then he can automatically view it.
        return True

    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='view_page',
        check_global=False,
    )
    return has_perm


@cached_func
@auth_permission_required('change_page')
def user_can_view_page_draft(user, page, site=None):
    has_perm = has_generic_permission(
        page=page,
        user=user,
        action='change_page',
        site=site,
    )
    return has_perm


@cached_func
@auth_permission_required('change_page')
def user_can_change_all_pages(user, site):
    return has_global_permission(user, site, action='change_page')


@auth_permission_required('change_page')
def user_can_change_at_least_one_page(user, site, use_cache=True):
    perm_tuples = get_change_perm_tuples(
        user=user,
        site=site,
        check_global=True,
        use_cache=use_cache,
    )
    return perm_tuples == GRANT_ALL_PERMISSIONS or bool(perm_tuples)


@cached_func
def user_can_view_all_pages(user, site):
    if user.is_superuser:
        return True

    if not get_cms_setting('PERMISSION'):
        public_for = get_cms_setting('PUBLIC_FOR')
        can_see_unrestricted = public_for == 'all' or (public_for == 'staff' and user.is_staff)
        return can_see_unrestricted

    if not user.is_authenticated:
        return False

    if user.has_perm(PAGE_VIEW_CODENAME):
        # This is for backwards compatibility.
        # The previous system allowed any user with the explicit view_page
        # permission to see all pages.
        return True

    if user_can_change_all_pages(user, site):
        # If a user can change all pages then he can see all pages.
        return True
    return has_global_permission(user, site, action='view_page')


def _perm_tuples_to_ids(perm_tuples):
    import inspect
    import warnings

    from django.db.models import Q

    fn_name = "_".join(inspect.stack()[1][3].split("_")[:-1])  # Calling function's name
    warnings.warn(f"{fn_name}_ids is deprecated. Use {fn_name}_perm_tuples instead.",
                  RemovedInDjangoCMS43Warning, stacklevel=3)

    allowed_pages = Q()
    for perm in perm_tuples:
        allowed_pages |= PermissionTuple(perm).allow_list("node")

    return list(Page.objects.filter(allowed_pages).values_list('pk', flat=True))


def get_add_perm_tuples(user, site, check_global=True, use_cache=True):
    """
    Give a list of page where the user has add page rights or the string
    "All" if the user has all rights.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='add_page',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_add_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_add_perm_tuples(user, site, check_global=check_global, use_cache=use_cache)
    return _perm_tuples_to_ids(perm_tuples)


def get_change_perm_tuples(user, site, check_global=True, use_cache=True):
    """
    Give a list of page where the user has edit rights or the string "All" if
    the user has all rights.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='change_page',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_change_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_change_perm_tuples(user, site, check_global=check_global, use_cache=use_cache)
    return _perm_tuples_to_ids(perm_tuples)


def get_change_advanced_settings_perm_tuples(user, site, check_global=True, use_cache=True):
    """
    Give a list of page where the user can change advanced settings or the
    string "All" if the user has all rights.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='change_page_advanced_settings',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_change_advanced_settings_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_change_advanced_settings_perm_tuples(
        user=user,
        site=site,
        check_global=check_global,
        use_cache=use_cache,
    )
    return _perm_tuples_to_ids(perm_tuples)


def get_change_permissions_perm_tuples(user, site, check_global=True, use_cache=True):
    """Give a list of page where the user can change permissions.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='change_page_permissions',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_change_permissions_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_change_permissions_perm_tuples(
        user=user,
        site=site,
        check_global=check_global,
        use_cache=use_cache,
    )
    return _perm_tuples_to_ids(perm_tuples)


def get_delete_perm_tuples(user, site, check_global=True, use_cache=True):
    """
    Give a list of page where the user has delete rights or the string "All" if
    the user has all rights.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='delete_page',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_delete_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_delete_perm_tuples(user, site, check_global=check_global, use_cache=use_cache)
    return _perm_tuples_to_ids(perm_tuples)


def get_move_page_perm_tuples(user, site, check_global=True, use_cache=True):
    """Give a list of pages which user can move.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='move_page',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_move_page_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_move_page_perm_tuples(user, site, check_global=check_global, use_cache=use_cache)
    return _perm_tuples_to_ids(perm_tuples)


def get_publish_perm_tuples(user, site, check_global=True, use_cache=True):
    """
    Give a list of page where the user has publish rights or the string "All" if
    the user has all rights.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='publish_page',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_publish_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_publish_perm_tuples(user, site, check_global=check_global, use_cache=use_cache)
    return _perm_tuples_to_ids(perm_tuples)


def get_view_perm_tuples(user, site, check_global=True, use_cache=True):
    """Give a list of pages which user can view.
    """
    perm_tuples = _get_page_permission_tuples_for_action(
        user=user,
        site=site,
        action='view_page',
        check_global=check_global,
        use_cache=use_cache,
    )
    return perm_tuples


def get_view_ids(user, site, check_global=True, use_cache=True):
    perm_tuples = get_view_perm_tuples(user, site, check_global=check_global, use_cache=use_cache)
    return _perm_tuples_to_ids(perm_tuples)


def has_generic_permission(page, user, action, site=None, check_global=True, use_cache=True):
    if site is None:
        site = get_current_site()

    page_path = page.node.path
    actions_map = {
        'add_page': get_add_perm_tuples,
        'change_page': get_change_perm_tuples,
        'change_page_advanced_settings': get_change_advanced_settings_perm_tuples,
        'change_page_permissions': get_change_permissions_perm_tuples,
        'delete_page': get_delete_perm_tuples,
        'delete_page_translation': get_delete_perm_tuples,
        'publish_page': get_publish_perm_tuples,
        'move_page': get_move_page_perm_tuples,
        'view_page': get_view_perm_tuples,
    }

    func = actions_map[action]

    page_perms = func(user, site, check_global=check_global, use_cache=use_cache)
    return page_perms == GRANT_ALL_PERMISSIONS or any(
        PermissionTuple(perm).contains(page_path) for perm in page_perms
    )
