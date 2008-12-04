from cms import settings

def media(request):
    """
    Adds media-related context variables to the context.
    """
    return {'CMS_MEDIA_URL': settings.CMS_MEDIA_URL}
