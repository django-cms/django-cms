# -*- coding: utf-8 -*-
import os

gettext = lambda s: s


urlpatterns = []


def configure(**extra):
    from django.conf import settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cms.test_utils.cli'
    defaults = dict(
        CACHE_BACKEND = 'locmem:///',
        DEBUG = True,
        TEMPLATE_DEBUG = True,
        DATABASE_SUPPORTS_TRANSACTIONS = True,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        SITE_ID = 1,
        USE_I18N = True,
        MEDIA_ROOT = '/media/',
        STATIC_ROOT = '/static/',
        CMS_MEDIA_ROOT = '/cms-media/',
        CMS_MEDIA_URL = '/cms-media/',
        MEDIA_URL = '/media/',
        STATIC_URL = '/static/',
        ADMIN_MEDIA_PREFIX = '/static/admin/',
        EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend',
        SECRET_KEY = 'key',
        TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.eggs.Loader',
        ),
       TEMPLATE_CONTEXT_PROCESSORS = [
            "django.contrib.auth.context_processors.auth",
            "django.core.context_processors.i18n",
            "django.core.context_processors.debug",
            "django.core.context_processors.request",
            "django.core.context_processors.media",
            'django.core.context_processors.csrf',
            "cms.context_processors.media",
            "sekizai.context_processors.sekizai",
            "django.core.context_processors.static",
        ],
        TEMPLATE_DIRS = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'project', 'templates'))
        ],
        MIDDLEWARE_CLASSES = [
            'django.contrib.sessions.middleware.SessionMiddleware',
            'cms.middleware.multilingual.MultilingualURLMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.doc.XViewMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
        ],
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'cms',
            'menus',
            'mptt',
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
            'cms.test_utils.project.sampleapp',
            'cms.test_utils.project.placeholderapp',
            'cms.test_utils.project.pluginapp',
            'cms.test_utils.project.pluginapp.plugins.manytomany_rel',
            'cms.test_utils.project.fakemlng',
            'cms.test_utils.project.fileapp',
            'south',
            'reversion',
            'sekizai',
        ],
        LANGUAGE_CODE = "en",
        LANGUAGES = (
            ('en', gettext('English')),
            ('fr', gettext('French')),
            ('de', gettext('German')),
            ('pt-BR', gettext("Brazil")),
            ('nl', gettext("Dutch")),
        ),
        CMS_LANGUAGES = (
            ('en', gettext('English')),
            ('fr', gettext('French')),
            ('de', gettext('German')),
            ('pt-BR', gettext("Brazil")),
            ('nl', gettext("Dutch")),
        ),
        CMS_LANGUAGE_CONF = {
            'de':['fr', 'en'],
            'en':['fr', 'de'],
        },
        CMS_SITE_LANGUAGES = {
            1:['en','de','fr','pt-BR'],
            2:['de','fr'],
            3:['nl'],
        },
        CMS_TEMPLATES = (
            ('col_two.html', gettext('two columns')),
            ('col_three.html', gettext('three columns')),
            ('nav_playground.html', gettext('navigation examples')),
        ),
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
        },
        CMS_SOFTROOT = True,
        CMS_MODERATOR = True,
        CMS_PERMISSION = True,
        CMS_PUBLIC_FOR = 'all',
        CMS_CACHE_DURATIONS = {
            'menus': 0,
            'content': 0,
            'permissions': 0,
        },
        CMS_APPHOOKS=[],
        CMS_REDIRECTS = True,
        CMS_SEO_FIELDS = True,
        CMS_FLAT_URLS = False,
        CMS_MENU_TITLE_OVERWRITE = True,
        CMS_HIDE_UNTRANSLATED = False,
        CMS_URL_OVERWRITE = True,
        CMS_SHOW_END_DATE = True,
        CMS_SHOW_START_DATE = True,
        CMS_PLUGIN_PROCESSORS = tuple(),
        CMS_PLUGIN_CONTEXT_PROCESSORS = tuple(),
        CMS_SITE_CHOICES_CACHE_KEY = 'CMS:site_choices',
        CMS_PAGE_CHOICES_CACHE_KEY = 'CMS:page_choices',
        SOUTH_TESTS_MIGRATE = False,
        CMS_NAVIGATION_EXTENDERS = (
            ('cms.test_utils.project.sampleapp.menu_extender.get_nodes', 'SampleApp Menu'),
        ),
        TEST_RUNNER = 'cms.test_utils.runners.NormalTestRUnner',
        JUNIT_OUTPUT_DIR = '.',
        TIME_TESTS = False,
        ROOT_URLCONF = 'cms.test_utils.cli',
    )
    defaults.update(extra)
    settings.configure(**defaults)
    from cms.conf import patch_settings
    patch_settings()
    from south.management.commands import patch_for_test_db_setup
    patch_for_test_db_setup()
    from django.core.urlresolvers import set_urlconf
    from django.contrib import admin
    admin.autodiscover()
    set_urlconf(settings.ROOT_URLCONF)
