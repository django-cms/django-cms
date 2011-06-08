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

#Hide untranslated Pages
CMS_HIDE_UNTRANSLATED = True

#Fall back to another language if the requested page isn't available in the preferred language
CMS_LANGUAGE_FALLBACK = True

#Configuration on how to order the fallbacks for languages.
# example: {'de': ['en', 'fr'],
#           'en': ['de'],
#          }
CMS_LANGUAGE_CONF = {}

# Defines which languages should be offered.
CMS_LANGUAGES = settings.LANGUAGES

# If you have different sites with different languages you can configure them here
# and you will only be able to edit the languages that are actually on the site.
# example: {1:['en','de'],
#           2:['en','fr'],
#           3:['en'],}
CMS_SITE_LANGUAGES = {}

CMS_SITE_CHOICES_CACHE_KEY = 'CMS:site_choices'
CMS_PAGE_CHOICES_CACHE_KEY = 'CMS:page_choices'

# Languages that are visible in the frontend (Language Chooser)
CMS_FRONTEND_LANGUAGES = [x[0] for x in CMS_LANGUAGES]


# Path for CMS media (uses <MEDIA_ROOT>/cms by default)
CMS_MEDIA_PATH = 'cms/'
CMS_MEDIA_ROOT = os.path.join(settings.MEDIA_ROOT, CMS_MEDIA_PATH)
CMS_MEDIA_URL = os.path.join(settings.MEDIA_URL, CMS_MEDIA_PATH)

# Path (relative to MEDIA_ROOT/MEDIA_URL) to directory for storing page-scope files.
CMS_PAGE_MEDIA_PATH = 'cms_page_media/'

# moderator mode - if True, approve path can be setup for every page, so there
# will be some control over the published stuff
CMS_MODERATOR = False 

# Defines what character will be used for the __unicode__ handling of cms pages
CMS_TITLE_CHARACTER = '+'

# Enable non-cms placeholder frontend editing
PLACEHOLDER_FRONTEND_EDITING = True

# Cache prefix so one can deploy several sites on one cache server
CMS_CACHE_PREFIX = 'cms-'

# they are missing in the permission-merge2 branch
CMS_PLUGIN_PROCESSORS = tuple()
CMS_PLUGIN_CONTEXT_PROCESSORS = tuple()