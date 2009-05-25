from cms.models import Page, GlobalPagePermission, PagePermission, MASK_PAGE
from cms.exceptions import NoPermissionsException

def publish_page_request(page):
    page.status = Page.PUBLISHED
    page.save()
    
    
def get_user_level(user):
    """Returns highest user level from the page/permission hierarchy on which
    user haves some permissions. Also takes look into user groups. Higher 
    level equals lover number. Users on top of hierarchy have level 0. Level 
    is the same like page.level attribute. Checks if user haves permissions 
    granted on page he is assigned, if no, his level is increased.
    """
    if user.is_superuser or \
        GlobalPagePermission.objects.with_user(user).count():
        # those
        return 0
    try:
        permission = PagePermission.objects.with_user(user).order_by('page__level')[0]
    except IndexError:
        # user is'nt assigned to any node
        raise NoPermissionsException
    
    level = permission.page.level
    # granted on this page, or followers
    if not permission.grant_on & MASK_PAGE:
        # increase level
        level += 1
    return level
    