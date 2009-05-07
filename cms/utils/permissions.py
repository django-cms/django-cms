from cms.models import Page, PagePermission, GlobalPagePermission
from cms.exceptions import NoPermissionsException

def has_page_add_permission(request, page=None):
    """Return true if the current user has permission to add a new page.
    """        
    if request.user.is_superuser:
        return True
    
    opts = Page._meta
    if not request.user.has_perm(opts.app_label + '.' + opts.get_add_permission()):
        return False
    
    permissions = Page.permissions.get_change_id_list(request.user)
    if permissions is Page.permissions.GRANT_ALL:
        return True
    target = request.GET.get('target', -1)
    position = request.GET.get('position', None)
    if int(target) in permissions:
        if position == "first-child":
            return True
        else:
            if Page.objects.get(pk=target).parent_id in permissions:
                return True
    return False


def get_user_permission_level(user):
    """Returns highest user level from the page/permission hierarchy on which
    user haves can_change_permission. Also takes look into user groups. Higher 
    level equals to lover number. Users on top of fierarchy have level 0. Level 
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
    

def get_add_permission(self):
        return 'add_%s' % self.object_name.lower()

def get_change_permission(self):
    return 'change_%s' % self.object_name.lower()

def get_delete_permission(self):
    return 'delete_%s' % self.object_name.lower()

