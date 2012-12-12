# -*- coding: utf-8 -*-
from collections import defaultdict
from cms.exceptions import NoPermissionsException
from cms.models import Page, PagePermission, GlobalPagePermission, MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from cms.utils.plugins import current_site


try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

# thread local support
_thread_locals = local()

def set_current_user(user):
    """
    Assigns current user from request to thread_locals, used by
    CurrentUserMiddleware.
    """
    _thread_locals.user=user
    
def get_current_user():
    """
    Returns current user, or None
    """
    return getattr(_thread_locals, 'user', None)


def has_page_add_permission(request):
    """
    Return true if the current user has permission to add a new page. This is
    just used for general add buttons - only superuser, or user with can_add in
    globalpagepermission can add page.
    
    Special case occur when page is going to be added from add page button in
    change list - then we have target and position there, so check if user can
    add page under target page will occur. 
    """
    opts = Page._meta
    if request.user.is_superuser:
        return True
    
    # if add under page
    target = request.GET.get('target', None)
    position = request.GET.get('position', None)
    
    if target is not None:
        try:
            page = Page.objects.get(pk=target)
        except Page.DoesNotExist:
            return False
        if (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and
            has_global_page_permission(request, page.site_id, can_add=True)):
            return True
        if position in ("first-child", "last-child"):
            return page.has_add_permission(request)
        elif position in ("left", "right"):
            if page.parent_id:
                return has_generic_permission(page.parent_id, request.user, "add", page.site)
    else:
        from cms.utils.plugins import current_site
        site = current_site(request)
        if (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and
            has_global_page_permission(request, site, can_add=True)):
            return True
    return False


def has_any_page_change_permissions(request):
    from cms.utils.plugins import current_site
    if not request.user.is_authenticated():
        return False
    return request.user.is_superuser or PagePermission.objects.filter(
            page__site=current_site(request)
        ).filter((
            Q(user=request.user) |
            Q(group__in=request.user.groups.all())
        )).exists()


def has_page_change_permission(request):
    """
    Return true if the current user has permission to change this page.
    To be granted this permission, you need the cms.change_page permission.
    In addition, if CMS_PERMISSION is enabled you also need to either have
    global can_change permission or just on this page.
    """
    from cms.utils.plugins import current_site
    opts = Page._meta
    return request.user.is_superuser or (
        request.user.has_perm(opts.app_label + '.' + opts.get_change_permission())
        and (
            not settings.CMS_PERMISSION or
            has_global_page_permission(request, current_site(request),
                                       can_change=True) or
            has_any_page_change_permissions(request)))


def has_global_page_permission(request, site=None, **filters):
    """
    A helper function to check for global page permissions for the current user
    and site. Caches the result on a request basis, so multiple calls to this
    function inside of one request/response cycle only generate one query.

    :param request: the Request object
    :param site: the Site object or ID
    :param filters: queryset filters, e.g. ``can_add = True``
    :return: ``True`` or ``False``
    """
    if not request.user.is_authenticated():
        return False
    if not settings.CMS_PERMISSION or request.user.is_superuser:
        return True
    if not hasattr(request, '_cms_global_perms'):
        request._cms_global_perms = {}
    key = tuple((k, v) for k, v in filters.iteritems())
    if site:
        key = (('site', site.pk if hasattr(site, 'pk') else int(site)),) + key
    if key not in request._cms_global_perms:
        qs = GlobalPagePermission.objects.with_user(request.user).filter(**filters)
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
        permission = PagePermission.objects.with_can_change_permissions(user).order_by('page__level')[0]
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
        return User.objects.all() 
    site = Site.objects.get_current()
    page_id_allow_list = Page.permissions.get_change_permissions_id_list(user, site)
    try:
        user_level = get_user_permission_level(user)
    except NoPermissionsException:
        # no permission so only staff and no page permissions 
        qs = User.objects.distinct().filter(
                Q(is_staff=True) & 
                Q(pageuser__created_by=user) & 
                Q(pagepermission__page=None)
        )
        qs = qs.exclude(pk=user.id).exclude(groups__user__pk=user.id)
        return qs
    # normal query
    qs = User.objects.distinct().filter(
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
        qs = Group.objects.distinct().filter(
         Q(pageusergroup__created_by=user) & 
         Q(pagepermission__page=None)
        )
        return qs
    
    qs = Group.objects.distinct().filter(
         (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__level__gte=user_level)) 
        | (Q(pageusergroup__created_by=user) & Q(pagepermission__page=None))
    )
    return qs

def has_global_change_permissions_permission(request):
    opts = GlobalPagePermission._meta
    user = request.user
    if user.is_superuser or (
        user.has_perm(opts.app_label + '.' + opts.get_change_permission()) and
        has_global_page_permission(request, can_change_permissions=True)):
        return True
    return False

def has_generic_permission(page_id, user, attr, site):
    """
    Permission getter for single page with given id.
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
    pages_list.sort(key=lambda page: (page.tree_id, page.lft))
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
    if not settings.CMS_PERMISSION:
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


def has_view_permission(request, page):
    can_see_unrestricted = settings.CMS_PUBLIC_FOR == 'all' or (
        settings.CMS_PUBLIC_FOR == 'staff' and request.user.is_staff)

    # inherited and direct view permissions
    is_restricted = bool(get_any_page_view_permissions(request, page))

    if not is_restricted and can_see_unrestricted:
        return True
    elif not request.user.is_authenticated():
        return False

    # Django wide auth perms "can_view" or cms auth perms "can_view"
    opts = page._meta
    codename = '%s.view_%s' % (opts.app_label, opts.object_name.lower())
    if not is_restricted:
        # a global permission was given to the request's user
        if has_global_page_permission(request, page.site_id, can_view=True):
            return True
    else:
        # a specific permission was granted to the request's user
        if page.get_draft_object().has_generic_permission(request, "view"):
            return True

    # The user has a normal django permission to view pages globally
    return request.user.has_perm(codename)


def load_view_restrictions(request, pages):
    """ Load all view restrictions for the pages and update the cache in the request
    The request cache will receive values for all the pages, but the returned
    dict will only have keys where restrictions actually exist
    """
    restricted_pages = defaultdict(list)
    if settings.CMS_PERMISSION:
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
        page_permissions = PagePermission.objects.filter(page__in=pages_by_id).select_related('group__users')
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


def get_visible_pages(request, pages, site=None):
    """
     This code is basically a many-pages-at-once version of
     Page.has_view_permission.
     pages contains all published pages
     check if there is ANY restriction
     that needs a permission page visibility calculation
    """
    can_see_unrestricted = settings.CMS_PUBLIC_FOR == 'all' or (
        settings.CMS_PUBLIC_FOR == 'staff' and request.user.is_staff)
    is_auth_user = request.user.is_authenticated()

    restricted_pages = load_view_restrictions(request, pages)

    if not restricted_pages:
        if can_see_unrestricted:
            return pages
        elif not is_auth_user:
            return [] # Unauth user can't acquire global or user perm to see pages

    if is_auth_user and settings.CMS_PERMISSION:
        if not site:
            site = current_site(request)
        if has_global_page_permission(request, site, can_view=True):
            return pages

    def has_global_perm():
        if not settings.CMS_PERMISSION:
            return True
        if has_global_perm.cache < 0:
            has_global_perm.cache = bool(request.user.has_perm('cms.view_page'))
        return bool(has_global_perm.cache)
    has_global_perm.cache = -1

    def has_permission_membership(page):
        """
        PagePermission user group membership tests
        """
        user_pk = request.user.pk
        for perm in restricted_pages[page.pk]:
            if perm.user_id == user_pk:
                return True
            if not perm.group_id:
                continue
            if has_permission_membership.user_groups is None:
                has_permission_membership.user_groups = request.user.groups.all().values_list('pk', flat=True)
            if perm.group_id in has_permission_membership.user_groups:
                return True
        return False
    has_permission_membership.user_groups = None

    visible_pages = []
    for page in pages:
        to_add = False
        is_restricted = page.pk in restricted_pages
        # restricted_pages contains as key any page.pk that is
        # affected by a permission grant_on
        if not is_restricted and can_see_unrestricted:
            to_add = True
        elif is_auth_user:
            # setting based handling of unrestricted pages
            # check group and user memberships to restricted pages
            if is_restricted and has_permission_membership(page):
                to_add = True
            elif has_global_perm():
                to_add = True

        if to_add:
            visible_pages.append(page)

    return visible_pages


def get_user_sites_queryset(user):
    """
    Returns queryset of all sites available for given user.
    
    1.  For superuser always returns all sites.
    2.  For global user returns all sites he haves in global page permissions 
        together with any sites he is assigned to over an page.
    3.  For standard user returns just sites he is assigned to over pages.
    """
    qs = Site.objects.all()
    
    if user.is_superuser or not settings.CMS_PERMISSION:
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
    query |= Q(Q(page__pagepermission__user=user) | Q(page__pagepermission__group__user=user)) & \
        (Q(Q(page__pagepermission__can_add=True) | Q(page__pagepermission__can_change=True)))
    return qs.filter(query).distinct()


def has_plugin_permission(user, plugin_type, permission_type):
    """
    Checks that a user has permissions for the plugin-type given to perform
    the action defined in permission_type
    permission_type should be 'add', 'change' or 'delete'.
    """
    plugin_class = plugin_pool.get_plugin(plugin_type)
    plugin_model = plugin_class.model
    plugin_opts = plugin_model._meta
    return user.has_perm('%s.%s_%s' % (plugin_opts.app_label, permission_type,
                                      plugin_opts.object_name.lower()))
