# -*- coding: utf-8 -*-
import datetime
from cms.models import Page, PageModeratorState, CMSPlugin, Title
from cms.utils import timezone


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

    if force_moderation_action:
        PageModeratorState(user=user, page=page, action=force_moderation_action).save()
        page.save() # sets the page to dirty
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
    created = timezone.now() - datetime.timedelta(seconds=UPDATE_TOLERANCE)
    try:
        state = page.pagemoderatorstate_set.filter(user=user, created__gt=created).order_by('-created')[0]
    except IndexError:
        state = None
    if not state or state.message:
        # If no state was found or it already has a message, create a new one
        state = PageModeratorState(user=user, page=page, action=PageModeratorState.ACTION_CHANGED)

    state.message = message
    state.save()


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

