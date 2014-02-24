# -*- coding: utf-8 -*-
from cms.utils.conf import get_cms_setting
from django.conf import settings

def media(request):
    """
    Adds media-related context variables to the context.
    """
    return {'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL')}

def csrf_cookie_name(request):
	return {'CSRF_COOKIE_NAME': settings.CSRF_COOKIE_NAME}
