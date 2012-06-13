# Changes to reflect the removal of ADMIN_MEDIA_PREFIX in Django 1.4
try:
	from django import VERSION
	from django.conf import settings
	ADMIN_STATIC_PREFIX = settings.STATIC_URL + 'admin/'
	if VERSION < (1,4,0):
		ADMIN_STATIC_PREFIX = settings.ADMIN_MEDIA_PREFIX
except ImportError:
	pass