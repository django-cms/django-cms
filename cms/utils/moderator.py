# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting


def use_draft(request):
    if request:
        structure = get_cms_setting('CMS_TOOLBAR_URL__BUILD')
        is_staff = request.user.is_authenticated() and request.user.is_staff
        edit_mode_active = is_staff and request.session.get('cms_edit', False)
        structure_mode_active = is_staff and structure in request.GET
        return bool(edit_mode_active or structure_mode_active)
    return False


def get_model_queryset(model, request=None):
    """Decision function used in frontend - says which model should be used.
    Public models are used unless looking at preview or edit versions of the page.
    """
    if use_draft(request):
        return model.objects.drafts()
    return model.objects.public()


def get_title_queryset(request=None):
    from cms.models import Title

    return Title.objects.all()


def get_cmsplugin_queryset(request=None):
    from cms.models import CMSPlugin

    return CMSPlugin.objects.all()
