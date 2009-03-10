"""
Convenience module for access of custom pages application settings,
which enforces default settings when the main settings module does not
contain the appropriate settings.
"""
from os.path import join
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Which template should be used.
DEFAULT_CMS_TEMPLATE = getattr(settings, 'DEFAULT_CMS_TEMPLATE', None)
if DEFAULT_CMS_TEMPLATE is None:
    raise ImproperlyConfigured('Please make sure you specified a DEFAULT_CMS_TEMPLATE setting.')

# Could be set to None if you don't need multiple templates.
CMS_TEMPLATES = getattr(settings, 'CMS_TEMPLATES', None)
if CMS_TEMPLATES is None:
    CMS_TEMPLATES = ()

# Whether to enable permissions.
CMS_PERMISSION = getattr(settings, 'CMS_PERMISSION', True)

# Whether a slug should be unique together with its parent and in the same lanuage?
i18n_installed = not 'cms.middleware.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES
CMS_UNIQUE_SLUGS = getattr(settings, 'CMS_UNIQUE_SLUGS', i18n_installed)

# Wheter the cms has a softroot functionionality
CMS_SOFTROOT = getattr(settings, 'CMS_SOFTROOT', False)

# Wheter the cms uses django-reversion
CMS_REVISIONS = getattr(settings, 'CMS_REVISIONS', False)

# Whether to enable revisions.
CMS_CONTENT_REVISION = getattr(settings, 'CMS_CONTENT_REVISION', True)

# Defines which languages should be offered.
CMS_LANGUAGES = getattr(settings, 'CMS_LANGUAGES', settings.LANGUAGES)

# Defines which language should be used by default and falls back to LANGUAGE_CODE
CMS_DEFAULT_LANGUAGE = getattr(settings, 'CMS_DEFAULT_LANGUAGE', settings.LANGUAGE_CODE)[:2]

# Defines how long page content should be cached, including navigation and admin menu.
CMS_CONTENT_CACHE_DURATION = getattr(settings, 'CMS_CONTENT_CACHE_DURATION', 60)

# The id of default Site instance to be used for multisite purposes.
SITE_ID = getattr(settings, 'SITE_ID', 1)
DEBUG = getattr(settings, 'DEBUG', False)
MANAGERS = settings.MANAGERS
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
INSTALLED_APPS = settings.INSTALLED_APPS
LANGUAGES = settings.LANGUAGES

# if the request host is not found in the db, should the default site_id be used or not? False means yes
CMS_USE_REQUEST_SITE = getattr(settings, 'CMS_USE_REQUEST_SITE', False)

# You can exclude some placeholder from the revision process
CMS_CONTENT_REVISION_EXCLUDE_LIST = getattr(settings, 'CMS_CONTENT_REVISION_EXCLUDE_LIST', ())

# URL that handles pages' media and uses <MEDIA_ROOT>/pages by default.
CMS_MEDIA_URL = getattr(settings, 'CMS_MEDIA_URL', join(settings.MEDIA_URL, 'cms/'))

# Show the publication date field in the admin, allows for future dating
# Changing this from True to False could cause some weirdness.  If that is required,
# you should update your database to correct any future dated pages
CMS_SHOW_START_DATE = getattr(settings, 'CMS_SHOW_START_DATE', False)

# Show the publication end date field in the admin, allows for page expiration
# Changing this from True to False could cause some weirdness.  If that is required,
# you should update your database and null any pages with publication_end_date set.
CMS_SHOW_END_DATE = getattr(settings, 'CMS_SHOW_END_DATE', False)

# Whether the user can overwrite the url of a page
CMS_URL_OVERWRITE = getattr(settings, 'CMS_URL_OVERWRITE', True)

# a tuble with a python path to a function that returns a list of navigation nodes
CMS_NAVIGATION_EXTENDERS = getattr(settings, 'CMS_NAVIGATION_EXTENDERS', ())
