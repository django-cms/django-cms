

def use_draft(request):
    is_staff = (request.user.is_authenticated and request.user.is_staff)
    return is_staff and not request.session.get('cms_preview')


def get_model_queryset(model, request=None):
    """Decision function used in frontend - says which model should be used.
    Public models are used unless looking at preview or edit versions of the page.
    """
    if request and use_draft(request):
        return model.objects.drafts()
    return model.objects.public()


def get_title_queryset(request=None):
    from cms.models import Title

    return Title.objects.all()


def get_cmsplugin_queryset(request=None):
    from cms.models import CMSPlugin

    return CMSPlugin.objects.all()
