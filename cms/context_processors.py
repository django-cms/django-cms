# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting

def media(request):
    """
    Adds media-related context variables to the context.
    """
    return {'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL')}
