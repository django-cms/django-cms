import django

__version__ = 'test'

if django.VERSION < (3, 2):
    default_app_config = 'cms.apps.CMSConfig'
