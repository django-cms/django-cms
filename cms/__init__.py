__version__ = '3.11.0'

try:
    import django

    if django.VERSION < (3, 2):
        default_app_config = 'cms.apps.CMSConfig'

except ModuleNotFoundError:
    # dependencies not installed yet
    pass
