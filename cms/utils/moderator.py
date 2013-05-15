# -*- coding: utf-8 -*-
from cms.models import PageModeratorState, CMSPlugin, Title


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


def use_draft(request):
    if request:
        is_staff = request.user.is_authenticated() and request.user.is_staff
        edit_mode = is_staff and request.session.get('cms_edit', False)
        build_mode = is_staff and request.session.get('cms_build', False)
        return is_staff and edit_mode or build_mode
    return False


def get_model_queryset(model, request=None):
    """Decision function used in frontend - says which model should be used.
    Public models are used unless looking at preview or edit versions of the page.
    """
    if use_draft(request):
        return model.objects.drafts()
    return model.objects.public()

# queryset helpers for basic models

get_title_queryset = lambda request=None: Title.objects.all()  # not sure if we need to only grab public items here
get_cmsplugin_queryset = lambda request=None: CMSPlugin.objects.all()  # CMSPlugin is no longer extending from Publisher

