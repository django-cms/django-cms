from cms.models import Page, PagePermission, GlobalPagePermission
from cms.exceptions import NoPermissionsException
from django.contrib.auth.models import User, Group
from django.db.models import Q

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

# thread local support
_thread_locals = local()

def set_current_user(user):
    """Assigns current user from request to thread_locals, used by
    CurrentUserMiddleware.
    """
    _thread_locals.user=user

    
def get_current_user():
    """Returns current user, or None
    """
    return getattr(_thread_locals, 'user', None)


def has_page_add_permission(request):
    """Return true if the current user has permission to add a new page. This is
    just used for general add buttons - only superuser, or user with can_add in
    globalpagepermission can add page.
    
    
    Special case occur when page is going to be added from add page button in
    change list - then we have target and position there, so check if user can
    add page under target page will occur. 
    """        
    opts = Page._meta
    if request.user.is_superuser or \
        (request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()) and
            GlobalPagePermission.objects.with_user(request.user).filter(can_add=True)):
        return True
    
    # if add under page
    target = request.GET.get('target', None)
    position = request.GET.get('position', None)
    
    if target is not None:
        try:
            page = Page.objects.get(pk=target)
        except:
            return False
        if position == "first-child":
            return page.has_add_permission(request)
        elif position in ("left", "right"):
            return has_add_page_on_same_level_permission(request, page)
    return False
    
def get_user_permission_level(user):
    """Returns highest user level from the page/permission hierarchy on which
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
    if user.is_superuser or \
        GlobalPagePermission.objects.with_can_change_permissions(user).count():
        # those
        return 0
    try:
        permission = PagePermission.objects.with_can_change_permissions(user).order_by('page__level')[0]
    except IndexError:
        # user is'nt assigned to any node
        raise NoPermissionsException
    return permission.page.level

def get_subordinate_users(user):
    """Returns users queryset, containing all subordinate users to given user 
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
    if user.is_superuser or \
            GlobalPagePermission.objects.with_can_change_permissions(user):
        return User.objects.all() 
    
    page_id_allow_list = Page.permissions.get_change_permissions_id_list(user)
    user_level = get_user_permission_level(user)
    
    qs = User.objects.distinct().filter(
        Q(is_staff=True) &
        (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__level__gte=user_level)) 
        | (Q(extuser__created_by=user) & Q(pagepermission__page=None))
    )
    return qs

def get_subordinate_groups(user):
    """Simillar to get_subordinate_users, but returns queryset of Groups instead
    of Users.
    """
    if user.is_superuser or \
            GlobalPagePermission.objects.with_can_change_permissions(user):
        return Group.objects.all()
    
    page_id_allow_list = Page.permissions.get_change_permissions_id_list(user)
    user_level = get_user_permission_level(user)
    
    qs = Group.objects.distinct().filter(
         (Q(pagepermission__page__id__in=page_id_allow_list) & Q(pagepermission__page__level__gte=user_level)) 
        | (Q(extgroup__created_by=user) & Q(pagepermission__page=None))
    )
    return qs

def has_global_change_permissions_permission(user):
    opts = GlobalPagePermission._meta
    if user.is_superuser or \
        (user.has_perm(opts.app_label + '.' + opts.get_change_permission()) and
            GlobalPagePermission.objects.with_user(user).filter(can_change=True)):
        return True
    return False

def has_add_page_on_same_level_permission(request, page):
    """Checks if there can be page added under page parent.
    """
    try:
        return page.parent.has_add_permission(request)
    except AttributeError:
        pass
    return False