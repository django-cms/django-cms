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

# Whether to enable tagging. 
CMS_TAGGING = getattr(settings, 'CMS_TAGGING', False)

# Whether to only allow unique slugs.
CMS_UNIQUE_SLUG_REQUIRED = getattr(settings, 'CMS_UNIQUE_SLUG_REQUIRED', True)

CMS_SOFTROOT = getattr(settings, 'CMS_SOFTROOT', False)

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

# You can exclude some placeholder from the revision process
CMS_CONTENT_REVISION_EXCLUDE_LIST = getattr(settings, 'CMS_CONTENT_REVISION_EXCLUDE_LIST', ())

# Sanitize the user input with html5lib
CMS_SANITIZE_USER_INPUT = getattr(settings, 'CMS_SANITIZE_USER_INPUT', False)

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
