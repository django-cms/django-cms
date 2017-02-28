# -*- coding: utf-8 -*-
from cms.models import CMSPlugin, Title


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
