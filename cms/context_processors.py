# -*- coding: utf-8 -*-
from cms.models import PageEditLock
from cms.utils.conf import get_cms_setting
from cms.utils import get_template_from_request


def cms_settings(request):
    """
    Adds cms-related variables to the context.
    """

    return {
        'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        'CMS_TEMPLATE': lambda: get_template_from_request(request),
    }


def page_edit_lock(request):
    """
    Show a warning within the toolbar if the current page is already under edit by another user.

    """
    try:
        if not request.current_page:
            return {}
    except AttributeError:
        return {}

    in_edit_mode = False
    if request.toolbar:
        if request.toolbar.edit_mode or '/admin/cms/page/' in request.path:
            in_edit_mode = True

    current_editor = None
    page_is_locked = False
    page_id = request.current_page.id

    if in_edit_mode:
        try:
            page_edit_lock = PageEditLock.objects.get(page__id=page_id)
            current_editor = page_edit_lock.user
            if request.user != page_edit_lock.user:
                page_is_locked = True

        except PageEditLock.DoesNotExist:
            edit_lock = PageEditLock(page=request.current_page, user=request.user)
            edit_lock.save()

    return {
        'current_editor': current_editor,
        'page_is_locked': page_is_locked
    }
