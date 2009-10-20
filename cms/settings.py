"""
Convenience module for access of custom pages application settings,
which enforces default settings when the main settings module does not
contain the appropriate settings.
"""
from os.path import join
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy  as _

# Which templates should be used for extracting the placeholders?
# example: CMS_TEMPLATES = (('base.html', 'default template'),)
CMS_TEMPLATES = getattr(settings, 'CMS_TEMPLATES', None)
if CMS_TEMPLATES is None:
    raise ImproperlyConfigured('Please make sure you specified a CMS_TEMPLATES setting.')

CMS_TEMPLATE_INHERITANCE = getattr(settings, 'CMS_TEMPLATE_INHERITANCE', True)
CMS_TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'
if CMS_TEMPLATE_INHERITANCE:
    # Append the magic inheritance template
    CMS_TEMPLATES = tuple([x for x in CMS_TEMPLATES]+[(CMS_TEMPLATE_INHERITANCE_MAGIC,
                    _('Inherit the template of the nearest ancestor'))])

# Define which placeholders support which plugins. Extra context will appear in the context of the plugins
# example:
#CMS_PLACEHOLDER_CONF = {
#    'placeholder1': {
#        "plugins": ('plugin1', 'plugin2'),
#        "extra_context": {},
#    },
#    'placeholder2': {
#        "plugins": ('plugin1', 'plugin3'),
#        "extra_context": {},
#    },
#}
CMS_PLACEHOLDER_CONF = getattr(settings, 'CMS_PLACEHOLDER_CONF', {})

# Whether to enable permissions.
CMS_PERMISSION = getattr(settings, 'CMS_PERMISSION', False)

# check if is user middleware installed
if CMS_PERMISSION and not 'cms.middleware.user.CurrentUserMiddleware' in settings.MIDDLEWARE_CLASSES:
    raise ImproperlyConfigured('CMS Permission system requires cms.middleware.user.CurrentUserMiddleware.\n'
        'Please put it into your MIDDLEWARE_CLASSES in settings file')
    
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

# Allow to overwrite the menu title
CMS_MENU_TITLE_OVERWRITE = getattr(settings, 'CMS_MENU_TITLE_OVERWRITE', False)

# Are redirects activated?
CMS_REDIRECTS = getattr(settings, 'CMS_REDIRECTS', False)

# Allow the description, title and keywords meta tags to be edited from the
# admin
CMS_SEO_FIELDS = getattr(settings, 'CMS_SEO_FIELDS', False) 

# a tuble with a python path to a function that returns a list of navigation nodes
CMS_NAVIGATION_EXTENDERS = getattr(settings, 'CMS_NAVIGATION_EXTENDERS', ())

# a tuple with a python path to a function that receives all navigation nodes and can add or remove them
CMS_NAVIGATION_MODIFIERS = getattr(settings, 'CMS_NAVIGATION_MODIFIERS', ())

# a tuple of hookable applications, e.g.:
# CMS_APPLICATIONS_URLS = (
#    ('sampleapp.urls', 'Sample application'),
# )
CMS_APPLICATIONS_URLS = getattr(settings, 'CMS_APPLICATIONS_URLS', ()) 

# Whether a slug should be unique ... must be unique in all languages.
i18n_installed = 'cms.middleware.multilingual.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES
CMS_UNIQUE_SLUGS = getattr(settings, 'CMS_UNIQUE_SLUGS', not i18n_installed)

#Should the tree of the pages be also be displayed in the urls? or should a flat slug structure be used?
CMS_FLAT_URLS = getattr(settings, 'CMS_FLAT_URLS', False)

# Wheter the cms has a softroot functionionality
CMS_SOFTROOT = getattr(settings, 'CMS_SOFTROOT', False)

#Hide untranslated Pages
CMS_HIDE_UNTRANSLATED = getattr(settings, 'CMS_HIDE_UNTRANSLATED', True)

#Fall back to another language if the requested page isn't available in the preferred language
CMS_LANGUAGE_FALLBACK = getattr(settings, 'CMS_LANGUAGE_FALLBACK', True)

#Configuration on how to order the fallbacks for languages.
# example: {'de': ['en', 'fr'],
#           'en': ['de'],
#          }
CMS_LANGUAGE_CONF = getattr(settings, 'CMS_LANGUAGE_CONF', {})

# Defines which languages should be offered.
CMS_LANGUAGES = getattr(settings, 'CMS_LANGUAGES', settings.LANGUAGES)

# Defines how long page content should be cached, including navigation
CMS_CONTENT_CACHE_DURATION = getattr(settings, 'CMS_CONTENT_CACHE_DURATION', 60)

# The id of default Site instance to be used for multisite purposes.
SITE_ID = getattr(settings, 'SITE_ID', 1)
DEBUG = getattr(settings, 'DEBUG', False)
MANAGERS = settings.MANAGERS
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
INSTALLED_APPS = settings.INSTALLED_APPS
LANGUAGES = settings.LANGUAGES


# Path for CMS media (uses <MEDIA_ROOT>/cms by default)
CMS_MEDIA_PATH = getattr(settings, 'CMS_MEDIA_PATH', 'cms/')
CMS_MEDIA_ROOT = getattr(settings, 'CMS_MEDIA_ROOT', join(settings.MEDIA_ROOT, CMS_MEDIA_PATH))
CMS_MEDIA_URL = getattr(settings, 'CMS_MEDIA_URL', ''.join((settings.MEDIA_URL, CMS_MEDIA_PATH)))

# Path (relative to MEDIA_ROOT/MEDIA_URL) to directory for storing page-scope files.
CMS_PAGE_MEDIA_PATH = getattr(settings, 'CMS_PAGE_MEDIA_PATH', 'cms_page_media/')

# moderator mode - if True, approve path can be setup for every page, so there
# will be some control over the published stuff
CMS_MODERATOR = getattr(settings, 'CMS_MODERATOR', False) 

#if CMS_MODERATOR and not CMS_PERMISSION:
#    raise ImproperlyConfigured('CMS Moderator requires permissions to be enabled')