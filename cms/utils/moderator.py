# -*- coding: utf-8 -*-
import datetime
from django.utils.translation import ugettext as _
from cms.models import Page, PageModeratorState, PageModerator, CMSPlugin, Title


I_APPROVE = 100 # current user should approve page
I_APPROVE_DELETE = 200

def page_changed(page, old_page=None, force_moderation_action=None):
    """Called from page post save signal. If page already had pk, old version
    of page is provided in old_page argument.
    """
    # Only record changes on the draft version
    if not page.publisher_is_draft:
        return
    # get user from thread locals
    from cms.utils.permissions import get_current_user
    user = get_current_user()

    force_moderation_action = force_moderation_action or getattr(page, 'force_moderation_action', None)
    if force_moderation_action:
        PageModeratorState(user=user, page=page, action=force_moderation_action).save()
        return

    if not old_page:
        # just newly created page
        PageModeratorState(user=user, page=page, action=PageModeratorState.ACTION_ADD).save()



def update_moderation_message(page, message):
    """This is bit special.. It updates last page state made from current user
    for given page. Its called after page is saved - page state is created when
    page gets saved (in signal), so this might have a concurrency issue, but 
    probably will work in 99,999%.
    
    If any page state isn't found in last UPDATE_TOLERANCE seconds, a new state
    will be created instead of affecting old message.    
    """

    UPDATE_TOLERANCE = 30 # max in last 30 seconds

    from cms.utils.permissions import get_current_user
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
    state, label = page.moderator_state, ""

    under_moderation = page.get_moderator_queryset()

    # TODO: OPTIMIZE!! calls 1 or 2 q per list item (page)

    if state == Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS:
        label = _('parent first')
    elif page.requires_approvement() and page.has_publish_permission(request) \
        and under_moderation.filter(user=request.user).count() \
        and not page.pagemoderatorstate_set.filter(user=request.user, action=PageModeratorState.ACTION_APPROVE).count():
            # only if he didn't approve already...
            is_delete = state == Page.MODERATOR_NEED_DELETE_APPROVEMENT
            state = is_delete and I_APPROVE_DELETE or I_APPROVE
            label = is_delete and _('delete') or _('approve')

    elif not page.is_approved():
        # if no moderator, we have just 2 states => changed / unchanged
        state = Page.MODERATOR_NEED_APPROVEMENT

    if not page.is_approved() and not label:
        if under_moderation.count():
            label = dict(page.moderator_state_choices)[state]            
    return dict(state=state, label=label)


def moderator_should_approve(request, page):
    """Says if user should approve given page. (just helper)
    """
    return page_moderator_state(request, page)['state'] >= I_APPROVE


def requires_moderation(page):
    """Returns True if page requires moderation
    """
    return bool(page.get_moderator_queryset().count())

def will_require_moderation(target_id, position):
    """Check if newly added page will require moderation
    """
    target = Page.objects.get(pk=target_id)
    if position == 'first-child':
        return requires_moderation(target)
    elif position in ('left', 'right'):
        if target.parent:
            return requires_moderation(target.parent)
    return False


def get_test_moderation_level(page, user=None, include_user=True):
    """Returns min moderation level for page, and result of user test if 
    user is given, so output is always tuple of:
        
        (moderation_level, requires_approvement)
        
    Meaning of requires_approvement is - somebody of higher instance must 
    approve changes made on this page by given user. 
    
    NOTE: May require some optimization, might call 3 huge sql queries in 
    worse case
    """

    qs = page.get_moderator_queryset()

    if user and user.is_superuser:
        if include_user and qs.filter(user__id=user.id, moderate_page=True).count():
            return 0, True
        return 0, False

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

    try:
        moderator = qs.select_related()[0]
    except IndexError:
        return PageModerator.MAX_MODERATION_LEVEL, False
    return moderator.page.level, True


def get_model_queryset(model, request=None):
    """Decision function used in frontend - says which model should be used.
    Public models are used unless looking at preview or edit versions of the page.
    """
    if request:
        preview_draft = ('preview' in request.GET and 'draft' in request.GET)
        edit_mode = ('edit' in request.GET or request.session.get('cms_edit', False))
        if preview_draft or edit_mode:    
            return model.objects.drafts()
    # Default case / moderator is used but there is no request
    return model.objects.public()

# queryset helpers for basic models
#get_page_queryset = lambda request=None: get_model_queryset(Page, request)
get_title_queryset = lambda request=None: Title.objects.all()   # not sure if we need to only grab public items here
get_cmsplugin_queryset = lambda request=None: CMSPlugin.objects.all()   # CMSPlugin is no longer extending from Publisher

