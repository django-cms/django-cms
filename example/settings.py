# Django settings for cms project.
import os
PROJECT_DIR = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

CACHE_BACKEND = 'locmem:///'

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'#'postgresql_psycopg2'       # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'cms'           # Or path to database file if using sqlite3.
DATABASE_USER = 'cms'           # Not used with sqlite3.
DATABASE_PASSWORD = 'cms'       # Not used with sqlite3.
DATABASE_HOST = ''     # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''              # Set to empty string for default. Not used with sqlite3.

# Test database settings
TEST_DATABASE_CHARSET = "utf8"
TEST_DATABASE_COLLATION = "utf8_general_ci"

DATABASE_SUPPORTS_TRANSACTIONS = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(PROJECT_DIR, '../cms/media/')
#ADMIN_MEDIA_ROOT = os.path.join(PROJECT_DIR, '../admin_media/')
MEDIA_URL = '/media/'

ADMIN_MEDIA_PREFIX = '/media/admin/'

FIXTURE_DIRS = [os.path.join(PROJECT_DIR, 'fixtures')]

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*xq7m@)*f2awoj!spa0(jibsrz9%c0d=e(g)v*!17y(vx0ue_3'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.i18n",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    "cms.context_processors.media",
)

INTERNAL_IPS = ('127.0.0.1',)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',

    #'django.contrib.csrf.middleware.CsrfMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.multilingual.MultilingualURLMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    
)

ROOT_URLCONF = 'example.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    #'tagging',
    
    'cms',
    'publisher',
    
    'cms.plugins.text',
    'cms.plugins.picture',
    'cms.plugins.file',
    'cms.plugins.flash',
    'cms.plugins.link',
    'cms.plugins.snippet',
    'cms.plugins.googlemap',
    'cms.plugins.teaser',
    'cms.plugins.video',
    'cms.plugins.twitter',
    'mptt',
    'reversion',
    #'example.categories',
    #'debug_toolbar',
    'south',
    # sample application
    'example.sampleapp',
    #'store',
)

LANGUAGE_CODE = "en"

gettext = lambda s: s

LANGUAGES = (
    ('fr', gettext('French')),
    ('de', gettext('German')),
    ('en', gettext('English')),
    ('pt-br', gettext("Brazil")),
)

CMS_LANGUAGE_CONF = {
    'de':['fr'],
    'en':['fr'],
}

CMS_TEMPLATES = (
    ('index.html', gettext('default')),
    ('nice.html', gettext('nice one')),
    ('cool.html', gettext('cool one')),
    ('long-folder-long/long-template-name.html', gettext('long')),
)

CMS_APPLICATIONS_URLS = (
    ('sampleapp.urls', 'Sample application'),
    ('sampleapp.urlstwo', 'Second sample application'),
)

CMS_PLACEHOLDER_CONF = {                        
    'right-column': {
        "plugins": ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin'),
        "extra_context": {"theme":"16_16"},
        "name":gettext("right column")
    },
    
    'body': {
        "plugins": ("VideoPlugin", "TextPlugin", ),
        "extra_context": {"theme":"16_5"},
        "name":gettext("body"),
    },
    'fancy-content': {
        "plugins": ('TextPlugin', 'LinkPlugin'),
        "extra_context": {"theme":"16_11"},
        "name":gettext("fancy content"),
    },
}


CMS_NAVIGATION_EXTENDERS = (('example.categories.navigation.get_nodes', 'Categories'),)

CMS_SOFTROOT = True
CMS_MODERATOR = True
CMS_PERMISSION = True
CMS_REDIRECTS = True
CMS_SEO_FIELDS = True
CMS_MENU_TITLE_OVERWRITE = True
CMS_HIDE_UNTRANSLATED = False


try:
    from local_settings import *
except ImportError:
    pass
