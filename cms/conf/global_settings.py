# -*- coding: utf-8 -*-
"""
Global cms settings, are applied if there isn't value defined in project
settings. All available settings are listed here. Please don't put any 
functions / test inside, if you need to create some dynamic values / tests, 
take look at cms.conf.patch
"""
import os
from django.conf import settings

# The id of default Site instance to be used for multisite purposes.
SITE_ID = 1

# Which templates should be used for extracting the placeholders?
# Empty by default, as we don't impose any rigid requirements on users.
# example: CMS_TEMPLATES = (('base.html', 'default template'),)
CMS_TEMPLATES = ()

# Should pages be allowed to inherit their parent templates?
CMS_TEMPLATE_INHERITANCE = True
# This is just a STATIC GLOBAL VAR
CMS_TEMPLATE_INHERITANCE_MAGIC = 'INHERIT'

CMS_PLACEHOLDER_CONF = {}

# Whether to enable permissions.
CMS_PERMISSION = False

# Decides if pages without any view restrictions are public by default, or staff only
CMS_PUBLIC_FOR = 'all' # or 'staff'

CMS_CACHE_DURATIONS = {
     # Menu cache duration
    'menus': getattr(settings, 'MENU_CACHE_DURATION', 60 * 60),
    # Defines how long page content should be cached
    'content': getattr(settings, 'CMS_CONTENT_CACHE_DURATION', 60),
    # Defines how long user permissions should be cached
    'permissions': 60 * 60,
}

# Show the publication date field in the admin, allows for future dating
# Changing this from True to False could cause some weirdness.  If that is required,
# you should update your database to correct any future dated pages
CMS_SHOW_START_DATE = False

# Show the publication end date field in the admin, allows for page expiration
# Changing this from True to False could cause some weirdness.  If that is required,
# you should update your database and null any pages with publication_end_date set.
CMS_SHOW_END_DATE = False

# Whether the user can overwrite the url of a page
CMS_URL_OVERWRITE = True

# Allow to overwrite the menu title
CMS_MENU_TITLE_OVERWRITE = False

# Are redirects activated?
CMS_REDIRECTS = False

# Allow the description, title and keywords meta tags to be edited from the
# admin
CMS_SEO_FIELDS = False 

# a tuple of python path to AppHook Classes. Overwrites the auto-discovered apphooks.
CMS_APPHOOKS = ()  

#Should the tree of the pages be also be displayed in the urls? or should a flat slug structure be used?
CMS_FLAT_URLS = False

# Wheter the cms has a softroot functionionality
CMS_SOFTROOT = False



# Defines which languages should be offered and what are the defaults
# example:
# CMS_LANGUAGES = {
#    1: [
#        {
#            'code': 'en',
#            'name': _('English'),
#            'fallbacks': ['de', 'fr'],
#            'public': True,
#            'hide_untranslated': True,
#            'redirect_on_fallback':False,
#            },
#        {
#            'code': 'de',
#            'name': _('Deutsch'),
#            'fallbacks': ['en', 'fr'],
#            'public': True,
#            },
#        {
#            'code': 'fr',
#            'public': False,
#            }
#    ],
#    'default': {
#        'fallbacks': ['en', 'de', 'fr'],
#        'redirect_on_fallback':True,
#        'public': False,
#        'hide_untranslated': False,
#        }
#}

#CMS_LANGUAGES = {}


CMS_SITE_CHOICES_CACHE_KEY = 'CMS:site_choices'
CMS_PAGE_CHOICES_CACHE_KEY = 'CMS:page_choices'


# Path for CMS media (uses <MEDIA_ROOT>/cms by default)
CMS_MEDIA_PATH = 'cms/'
CMS_MEDIA_ROOT = os.path.join(settings.MEDIA_ROOT, CMS_MEDIA_PATH)
CMS_MEDIA_URL = os.path.join(settings.MEDIA_URL, CMS_MEDIA_PATH)

# Path (relative to MEDIA_ROOT/MEDIA_URL) to directory for storing page-scope files.
CMS_PAGE_MEDIA_PATH = 'cms_page_media/'

# Defines what character will be used for the __unicode__ handling of cms pages
CMS_TITLE_CHARACTER = '+'

# Enable non-cms placeholder frontend editing
PLACEHOLDER_FRONTEND_EDITING = True

# Cache prefix so one can deploy several sites on one cache server
CMS_CACHE_PREFIX = 'cms-'

# they are missing in the permission-merge2 branch
CMS_PLUGIN_PROCESSORS = tuple()
CMS_PLUGIN_CONTEXT_PROCESSORS = tuple()