import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from cms import settings as cms_settings
from cms.models import Page, PageModeratorState
from cms.utils.permissions import get_current_user, get_user_permission_level


I_APPROVE = 100 # current user should approve page


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
    
    # TODO: if page was changed, remove all approvements from hiher instances,
    # but keep approvements by lover instances, if there are some
    

def update_moderation_message(page, message):
    """This is bit special.. It updates last page state made from current user
    for given page. Its called after page is saved - page state is created when
    page gets saved (in signal), so this might have a concurrency issue, but 
    probably will work in 99,999%.
    
    If any page state is'nt found in last UPDATE_TOLERANCE seconds, a new state
    will be created instead of affecting old message.    
    """
    
    UPDATE_TOLERANCE = 30 # max in last 30 seconds
    
    user = get_current_user()
    created = datetime.datetime.now() - datetime.timedelta(seconds=UPDATE_TOLERANCE)
    try:
        state = page.pagemoderatorstate_set.filter(user=user, created__gt=created).order_by('-created')[0]
        # just state without message!!
        assert not state.message  
    except (IndexError, AssertionError):
        state = PageModeratorState(user=user, page=page, action=PageModeratorState.ACTION_CHANGED)
    
    state.message = message
    state.save()
    
def page_moderator_state(request, page):
    """Return moderator page state from page.moderator_state, but also takes 
    look if current user is in the approvement path, and should approve the this 
    page. In this case return 100 as an state value. 
    
    Returns:
        dict(state=state, label=label)
    """
    state, label = page.moderator_state, None
    
    if cms_settings.CMS_MODERATOR:
        if state == Page.MODERATOR_NEED_APPROVEMENT and page.has_moderate_permission(request):
            try:
                page.pagemoderator_set.get(user=request.user)
                if not page.pagemoderatorstate_set.filter(user=request.user, action=PageModeratorState.ACTION_APPROVE).count():
                    # only if he didn't approve already...
                    state = I_APPROVE
                    label = _('approve')
            except ObjectDoesNotExist:
                pass
            
    elif not page.is_approved():
        # if no moderator, we have just 2 states => changed / unchanged
        state = Page.MODERATOR_NEED_APPROVEMENT
    
    if not label:
        label = dict(page.moderator_state_choices)[state]
    return dict(state=state, label=label)


def moderator_should_approve(request, page):
    """Says if user should approve given page. (just helper)
    """
    print ">> pms:", page_moderator_state(request, page)
    return page_moderator_state(request, page)['state'] is I_APPROVE


def get_test_moderation_level(page, user=None):
    """Returns min moderation level for page, and result of user test if 
    user is given, so output is always tuple of:
        
        (moderation_level, requires_approvement)
        
    Meaning of requires_approvement is - somebody of higher instance must 
    approve changes made on this page by given user. 
    
    NOTE: May require some optimization, might call 3 huge sql queries in 
    worse case
    """
    if not cms_settings.CMS_MODERATOR or (user and user.is_superuser):
        return 0, False
    
    qs = page.get_moderator_queryset()
        
    if qs.filter(user__is_superuser=True).count():
        return 0, True
    
    if user:
        if qs.filter(user__id=user.id, user__globalpagepermission__gt=0).count():
            return 0, False
        
        try:
            moderator = qs.filter(user__id=user.id).select_related()[0]
            return moderator.page.level, False
        except IndexError:
            pass
    else:
        if qs.filter(user__globalpagepermission__gt=0).count():
            return 0, True
            
    moderator = qs.select_related()[0]
    return moderator.page.level, True

def approve_page(request, page):
    """Main approving function. Two things can happen here, depending on user
    level:
    
    1.) User is somewhere in the approvement path, but not on the top. In this
    case just mark this page as approved by this user.
    
    2.) User is on top of approvement path. Draft page with all dependencies 
    will be `copied` to public model, page states log will be cleaned.  
    
    """
    moderation_level, moderation_required = get_test_moderation_level(page, request.user)
        
    if not moderator_should_approve(request, page):
        # escape soon if there isn't any approvement required by this user
        return
    
    if not moderation_required:
        # this is a second case - user can publish changes
        page.publish()
    else:
        # first case - just mark page as approved from this user
        PageModeratorState(user=request.user, page=page, action=PageModeratorState.ACTION_APPROVE).save() 
        
        
def get_page_model(request=None):
    """Decides which Page model should be used - Draft, or PublicPage depending
    on request. 
    
    !IMPORTANT: All scripts should request Page from here...
    """
    
    if request and 'preview' in request.GET and 'draft' in request.GET \
        and request.user.is_staff:
        return Page
    return Page.PublicModel