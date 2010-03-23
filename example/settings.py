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
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media/')

# Absolute path to the directory that holds media. 
# DO NOT ACTUALLY USE THIS IN YOUR OWN PROJECT!!!! THIS IS JUST FOR TESTING
CMS_MEDIA_ROOT = os.path.join(PROJECT_DIR, '../cms/media/cms/')
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
    'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.i18n",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    'django.core.context_processors.csrf',
    "cms.context_processors.media",
)

INTERNAL_IPS = ('127.0.0.1',)

MIDDLEWARE_CLASSES = (
    #'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'cms.middleware.multilingual.MultilingualURLMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware', 
    
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
    'menus',
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
    'cms.plugins.inherit',
    'mptt',
    'reversion',
    'example.sampleapp',
    #'debug_toolbar',
    'south',
)

gettext = lambda s: s

LANGUAGE_CODE = "en"

LANGUAGES = (
    ('fr', gettext('French')),
    ('de', gettext('German')),
    ('en', gettext('English')),
    ('pt-BR', gettext("Brazil")),
)

CMS_LANGUAGE_CONF = {
    'de':['fr', 'en'],
    'en':['fr', 'de'],
}

CMS_SITE_LANGUAGES = {
    1:['fr','de','en','pt-BR'],
    2:['de','en'],
}

APPEND_SLASH = True

CMS_TEMPLATES = (
    ('col_two.html', gettext('two columns')),
    ('col_three.html', gettext('three columns')),
    ('nav_playground.html', gettext('navigation examples')),
)



CMS_PLACEHOLDER_CONF = {
    'col_sidebar': {
        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin'),
        'name': gettext("sidebar column")
    },                    
                        
    'col_left': {
        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
        'name': gettext("left column")
    },                  
                        
    'col_right': {
        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
        'name': gettext("right column")
    },                     
                        
                        
                                              
#    'right-column': {
#        "plugins": ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin'),
#        "extra_context": {"width":940},
#        "name":gettext("right column")
#    },
    
#    'body': {
#        "extra_context": {"width":280},
#        "name":gettext("body"),
#    },
#    'fancy-content': {
#        "plugins": ('TextPlugin', 'LinkPlugin'),
#        "extra_context": {"width":"640"},
#        "name":gettext("fancy content custom name"),
#        "limits": {
#            "global": 3,
#            "TextPlugin": 1,
#        },
#    },
}

CMS_SOFTROOT = True
CMS_MODERATOR = True
CMS_PERMISSION = True
CMS_REDIRECTS = True
CMS_SEO_FIELDS = True
CMS_FLAT_URLS = False
CMS_MENU_TITLE_OVERWRITE = True
CMS_HIDE_UNTRANSLATED = False
CMS_URL_OVERWRITE = True


try:
    from local_settings import *
except ImportError:
    pass

"""wt ?
try:
    import coverage
    TEST_RUNNER='cms.tests.test_runner_with_coverage'
    COVERAGE_MODULES = [
        'cms',
        'cms.admin', 
        'cms.admin.change_list',
        'cms.admin.forms',
        'cms.admin.models',
        'cms.admin.permissionadmin',
        'cms.admin.useradmin',
        'cms.admin.utils',
        'cms.admin.views',
        'cms.admin.widgets',
        'cms.admin.dialog',
        'cms.admin.dialog.forms',
        'cms.admin.dialog.utils',
        'cms.admin.dialog.views',
        'cms.cache',
        'cms.cache.permissions',
        'cms.cache.signals',
        'cms.conf.global_settings',
        'cms.conf.patch',
        'cms.management.commands.publisher_publish',
        'cms.middleware.multilingual',
        'cms.middleware.page',
        'cms.middleware.user',
        'cms.migrations',
        'cms.models', 
        'cms.models.managers',
        'cms.models.moderatormodels',
        'cms.models.pagemodel',
        'cms.models.permissionmodels',
        'cms.models.pluginmodel',
        'cms.models.query',
        'cms.models.signals',
        'cms.models.titlemodels',
        'cms.sitemaps.cms_sitemap',
        'cms.templatetags.cms_admin',
        'cms.templatetags.cms_tags',
        'cms.templatetags.js',
        'cms.templatetags.mlurl',
        'cms.utils',
        'cms.utils.admin',
        'cms.utils.helpers',
        'cms.utils.i18n',
        'cms.utils.mail',
        'cms.utils.moderator',
        'cms.utils.navigation',
        'cms.utils.page',
        'cms.utils.permissions',
        'cms.utils.urlutils',
        'cms.appresolver',
        'cms.context_processors',
        'cms.plugin_base',
        'cms.plugin_pool',
        'cms.signals',
        'cms.urls',
        'cms.views',
        'publisher',
        'publisher.base',
        'publisher.errors',
        'publisher.manager',
        'publisher.models',
        'publisher.mptt_support',
        'publisher.options',
        'publisher.query',
        ]
except:
    pass
"""