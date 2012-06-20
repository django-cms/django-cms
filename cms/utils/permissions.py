# -*- coding: utf-8 -*-
from cms.exceptions import NoPermissionsException
from cms.models import Page, PagePermission, GlobalPagePermission
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _



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
            GlobalPagePermission.objects.with_user(request.user).filter(can_add=True, sites__in=[page.site_id])):
            return True
        if position in ("first-child", "last-child"):
            return page.has_add_permission(request)
        elif position in ("left", "right"):
            if page.parent_id:
                return has_generic_permission(page.parent_id, request.user, "add", page.site)
                #return page.parent.has_add_permission(request)
    else:
        from cms.utils.plugins import current_site
        site = current_site(request)
        if (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and
            GlobalPagePermission.objects.with_user(request.user).filter(can_add=True, sites__in=[site])):
            return True
    return False

def has_any_page_change_permissions(request):
    from cms.utils.plugins import current_site
    return PagePermission.objects.filter(
            page__site=current_site(request)
        ).filter((
            Q(user=request.user) |
            Q(group__in=request.user.groups.all())
        )).exists()

def has_page_change_permission(request):
    """
    Return true if the current user has permission to change any page. This is
    just used for building the tree - only superuser, or user with can_change in
    globalpagepermission can change a page.
    """
    from cms.utils.plugins import current_site
    opts = Page._meta
    if request.user.is_superuser or (
        request.user.has_perm(opts.app_label + '.' + opts.get_change_permission()) and (
            GlobalPagePermission.objects.with_user(request.user).filter(
                can_change=True, sites__in=[current_site(request)]
            ).exists()) or has_any_page_change_permissions(request)):
        return True
    return False

def get_any_page_view_permissions(request, page):
    """
    Used by the admin template tag is_restricted
    """
    return PagePermission.objects.for_page(page=page).filter(can_view=True)



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
        # user is'nt assigned to any node
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
    Simillar to get_subordinate_users, but returns queryset of Groups instead
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

def has_global_change_permissions_permission(user):
    opts = GlobalPagePermission._meta
    if user.is_superuser or (
        user.has_perm(opts.app_label + '.' + opts.get_change_permission()) and
            GlobalPagePermission.objects.with_user(user).filter(can_change=True)):
        return True
    return False

def has_generic_permission(page_id, user, attr, site):
    """
    Permission getter for single page with given id.
    """
    func = getattr(Page.permissions, "get_%s_id_list" % attr)
    permission = func(user, site)
    return permission == Page.permissions.GRANT_ALL or page_id in permission


def get_user_sites_queryset(user):
    """
    Returns queryset of all sites available for given user.
    
    1.  For superuser always returns all sites.
    2.  For global user returns all sites he haves in global page permissions 
        together with any sites he is assigned to over an page.
    3.  For standard user returns just sites he is assigned to over pages.
    """
    qs = Site.objects.all()
    
    if user.is_superuser:
        return qs
    
    global_ids = GlobalPagePermission.objects.with_user(user).filter(
        Q(can_add=True) | Q(can_change=True)
    ).values_list('id', flat=True)
    
    q = Q()
    if global_ids:
        q = Q(globalpagepermission__id__in=global_ids)
        # haves some global permissions assigned
        if not qs.filter(q).exists():
            # haves global permissions, but none of sites is specified,
            # so he haves access to all sites
            return qs
    
    # add some pages if he haves permission to add / change them
    q |= Q(Q(page__pagepermission__user=user) | Q(page__pagepermission__group__user=user)) & \
        (Q(Q(page__pagepermission__can_add=True) | Q(page__pagepermission__can_change=True)))
    return qs.filter(q).distinct()


def has_plugin_permission(user, plugin_type, permission_type):
    """
    Checks that a user has permissions for the plugin-type given to performe 
    the action defined in permission_type
    permission_type should be 'add', 'change' or 'delete'.
    """
    plugin_class = plugin_pool.get_plugin(plugin_type)
    plugin_model = plugin_class.model
    plugin_opts = plugin_model._meta
    return user.has_perm('%s.%s_%s' % (plugin_opts.app_label, permission_type,
                                      plugin_opts.object_name.lower()))
