# -*- coding: utf-8 -*-
from django.conf import settings
import django


ADMIN_STATIC = None
if django.version >= (1, 4, 0):
		ADMIN_STATIC =  settings.STATIC_URL + 'admin/'
	else:
		ADMIN_STATIC =  settings.ADMIN_MEDIA_PREFIX

def media(request):
    """
    Adds media-related context variables to the context.
    """
    return {'CMS_MEDIA_URL': settings.CMS_MEDIA_URL}

	
def django_version(request):
    return { 'django_version': django.VERSION }
	
def admin_static_location(request):
	return {'ADMIN_STATIC':ADMIN_STATIC}