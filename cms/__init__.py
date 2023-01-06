__version__ = '3.11.1'

try:
    import django

    if django.VERSION < (3, 2):
        default_app_config = 'cms.apps.CMSConfig'
except (ImportError, ModuleNotFoundError):
    # Allow setup.py to import __version__ before dependencies are installed
    pass
