import datetime
from cms.exceptions import NoPermissionsException
from cms.models import GlobalPagePermission, PagePermission, MASK_PAGE,\
    PageModeratorState
from cms.utils.permissions import get_current_user
    
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


def page_changed(page, old_page=None):
    """Called from page post save signal. If page already had pk, old version
    of page is provided in old_page argument.
    """
    # get user from thread locals
    user = get_current_user()
    
    if not old_page:
        # just newly created page
        PageModeratorState(user=user, page=page, action=PageModeratorState.ACTION_ADD).save()
    
    if (old_page is None and page.published) or \
        (old_page and not old_page.published == page.published):
        action = page.published and PageModeratorState.ACTION_PUBLISH or PageModeratorState.ACTION_UNPUBLISH
        PageModeratorState(user=user, page=page, action=action).save()
        

def update_moderation_message(page, message):
    """This is bit special.. It updates last page state made from current user
    for given page. Its called after page is saved - page state is created when
    page gets saved (in signal), so this might have a concurrency issue, but 
    probably will work in 99,999%.
    
    If any page state is'nt found in last UPDATE_TOLERANCE seconds, a new state
    will be created instead of affecting old message.    
    """
    print ">>> update message:", message
    
    UPDATE_TOLERANCE = 30 # max in last 30 seconds
    
    user = get_current_user()
    created = datetime.datetime.now() - datetime.timedelta(seconds=UPDATE_TOLERANCE)
    try:
        state = page.pagemoderatorstate_set.filter(user=user, created__gt=created).order_by('-created')[0]
        # just state without message!!
        assert state.message > "" 
    except (IndexError, AssertionError):
        state = PageModeratorState(user=user, page=page, action=PageModeratorState.ACTION_CHANGED)
    
    state.message = message
    state.save()
    
    