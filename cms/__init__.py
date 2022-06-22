import django

__version__ = '0.10.1'

if django.VERSION < (3, 2):
    default_app_config = 'cms.apps.CMSConfig'
