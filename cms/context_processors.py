# -*- coding: utf-8 -*-
from cms.utils.conf import get_setting
from django.conf import settings

def media(request):
    """
    Adds media-related context variables to the context.
    """
    return {'CMS_MEDIA_URL': get_setting('MEDIA_URL')}
