# Django settings for cms project.
from distutils.version import LooseVersion
import django
import os
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
)

CACHE_BACKEND = 'locmem:///'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'cms.sqlite',
    }
}

DATABASE_SUPPORTS_TRANSACTIONS = True

TIME_ZONE = 'America/Chicago'

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media/')
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static/')

CMS_MEDIA_ROOT = os.path.join(PROJECT_DIR, '../../cms/media/cms/')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

FIXTURE_DIRS = [os.path.join(PROJECT_DIR, 'fixtures')]

SECRET_KEY = '*xq7m@)*f2awoj!spa0(jibsrz9%c0d=e(g)v*!17y(vx0ue_3'

#TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.eggs.Loader',
#)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        'django.template.loaders.eggs.Loader',
    )),
)

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.i18n",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    'django.core.context_processors.csrf',
    "cms.context_processors.media",
    "sekizai.context_processors.sekizai",
]

INTERNAL_IPS = ('127.0.0.1',)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'cms.middleware.multilingual.MultilingualURLMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    
)

ROOT_URLCONF = 'project.urls'


TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'cms',
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
    'project.sampleapp',
    'project.placeholderapp',
    'project.pluginapp',
    'project.pluginapp.plugins.manytomany_rel',
    'project.fakemlng',
    'project.fileapp',
    'south',
    'reversion',
    'sekizai',
]

if LooseVersion(django.get_version()) >= LooseVersion('1.3'):
    INSTALLED_APPS.append('django.contrib.staticfiles')
    TEMPLATE_CONTEXT_PROCESSORS.append("django.core.context_processors.static")
else:
    INSTALLED_APPS.append('staticfiles')
    TEMPLATE_CONTEXT_PROCESSORS.append("staticfiles.context_processors.static")


gettext = lambda s: s

LANGUAGE_CODE = "en"

LANGUAGES = (
    ('en', gettext('English')),
    ('fr', gettext('French')),
    ('de', gettext('German')),
    ('pt-BR', gettext("Brazil")),
    ('nl', gettext("Dutch")),
)

CMS_LANGUAGE_CONF = {
    'de':['fr', 'en'],
    'en':['fr', 'de'],
}

CMS_SITE_LANGUAGES = {
    1:['en','de','fr','pt-BR'],
    2:['de','fr'],
    3:['nl'],
}

APPEND_SLASH = True

CMS_TEMPLATES = (
    ('col_two.html', gettext('two columns')),
    ('col_three.html', gettext('three columns')),
    ('nav_playground.html', gettext('navigation examples')),
)



CMS_PLACEHOLDER_CONF = {
    'col_sidebar': {
        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                    'TextPlugin', 'SnippetPlugin'),
        'name': gettext("sidebar column")
    },                    
                        
    'col_left': {
        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                    'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
        'name': gettext("left column")
    },                  
                        
    'col_right': {
        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                    'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
        'name': gettext("right column")
    },
    'extra_context': {
        "plugins": ('TextPlugin',),
        "extra_context": {"width": 250},
        "name": "extra context"
    },
}

CMS_SOFTROOT = True
CMS_MODERATOR = True
CMS_PERMISSION = True
CMS_PUBLIC_FOR = 'all'
CMS_CACHE_DURATIONS = {
    'menus': 0,
    'content': 0,
    'permissions': 0,
}
CMS_REDIRECTS = True
CMS_SEO_FIELDS = True
CMS_FLAT_URLS = False
CMS_MENU_TITLE_OVERWRITE = True
CMS_HIDE_UNTRANSLATED = False
CMS_URL_OVERWRITE = True
CMS_SHOW_END_DATE = True
CMS_SHOW_START_DATE = True

CMS_PLUGIN_PROCESSORS = tuple()

CMS_PLUGIN_CONTEXT_PROCESSORS = tuple()

SOUTH_TESTS_MIGRATE = False

CMS_NAVIGATION_EXTENDERS = (
    ('project.sampleapp.menu_extender.get_nodes', 'SampleApp Menu'),
)

try:
    from local_settings import *
except ImportError:
    pass
    
TEST_RUNNER = 'project.testrunner.CMSTestSuiteRunner'
TEST_OUTPUT_VERBOSE = True
