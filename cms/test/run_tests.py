import sys
import os

def configure_settings(is_test, test_args):
    
    failfast = False
    direct = False
    test_args = list(test_args)
    if '--direct' in test_args:
        test_args.remove('--direct')
        sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", ".."))
        
    if '--manage' in test_args:
        test_args.remove('--manage')

    test_labels = []
    
    test_args_enum = dict([ (val, idx) for idx, val in enumerate(test_args)])
    
    env_name = ''
    if '--toxenv' in test_args:
        env_name = test_args[test_args_enum['--toxenv']+1]
        test_args.remove('--toxenv')
        test_args.remove(env_name)
    
    if '--failfast' in test_args:
        test_args.remove('--failfast')
        failfast = True
        
    if is_test:
        for label in test_args:
            test_labels.append('cms.%s' % label)
                
        if not test_labels:
            test_labels.append('cms')
    
    from cms.test import project
    import cms
    
    PROJECT_DIR = os.path.abspath(os.path.dirname(project.__file__))
    
    MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')
    CMS_MEDIA_ROOT = os.path.join(os.path.abspath(os.path.dirname(cms.__file__)), 'media', 'cms')
    
    FIXTURE_DIRS = [os.path.join(PROJECT_DIR, 'fixtures')]
    
    TEMPLATE_DIRS = (
        os.path.join(PROJECT_DIR, 'templates'),
    )
    
    JUNIT_OUTPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(cms.__file__)), '..', 'junit-%s' % env_name)
        
    ADMINS = tuple()
    DEBUG = True
    
    gettext = lambda x: x
    
    from django.conf import settings
    
    settings.configure(
        PROJECT_DIR = PROJECT_DIR,
        DEBUG = DEBUG,
        TEMPLATE_DEBUG = DEBUG,
        
        ADMINS = ADMINS,
        
        CACHE_BACKEND = 'locmem:///',
        
        MANAGERS = ADMINS,
        
        DATABASE_ENGINE = 'sqlite3',
        DATABASE_NAME = 'cms.sqlite',
        
        TEST_DATABASE_CHARSET = "utf8",
        TEST_DATABASE_COLLATION = "utf8_general_ci",
        
        DATABASE_SUPPORTS_TRANSACTIONS = True,
        
        TIME_ZONE = 'America/Chicago',
        
        SITE_ID = 1,
        
        USE_I18N = True,
        
        MEDIA_ROOT = MEDIA_ROOT,
        
        CMS_MEDIA_ROOT = CMS_MEDIA_ROOT,
        
        MEDIA_URL = '/media/',
        
        ADMIN_MEDIA_PREFIX = '/media/admin/',
        
        EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend',
        
        FIXTURE_DIRS = FIXTURE_DIRS,
        
        SECRET_KEY = '*xq7m@)*f2awoj!spa0(jibsrz9%c0d=e(g)v*!17y(vx0ue_3',
        
        TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.eggs.Loader',
        ),
        
        TEMPLATE_CONTEXT_PROCESSORS = (
            "django.core.context_processors.auth",
            "django.core.context_processors.i18n",
            "django.core.context_processors.debug",
            "django.core.context_processors.request",
            "django.core.context_processors.media",
            'django.core.context_processors.csrf',
            "cms.context_processors.media",
        ),
        
        INTERNAL_IPS = ('127.0.0.1',),
        
        MIDDLEWARE_CLASSES = (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'cms.middleware.multilingual.MultilingualURLMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.doc.XViewMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'cms.middleware.media.PlaceholderMediaMiddleware', 
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            
        ),
        
        ROOT_URLCONF = 'cms.test.project.urls',
        
        TEMPLATE_DIRS = TEMPLATE_DIRS,
        
        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            
            'cms',
            
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
            
            'cms.test.apps.sampleapp',
            'cms.test.apps.placeholderapp',
            'cms.test.apps.pluginapp',
            'cms.test.apps.pluginapp.plugins.manytomany_rel',
            'cms.test.apps.fakemlng',
            
            'menus',
            'mptt',
            'reversion'
        ),
        
        gettext = lambda s: s,
        
        LANGUAGE_CODE = "en",
        
        LANGUAGES = (
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
        
        APPEND_SLASH = True,
        
        CMS_TEMPLATES = (
            ('col_two.html', gettext('two columns')),
            ('col_three.html', gettext('three columns')),
            ('nav_playground.html', gettext('navigation examples')),
        ),
        
        CMS_PLACEHOLDER_CONF = {
            'col_sidebar': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin'),
                'name': gettext("sidebar column"),
            },                    
                                
            'col_left': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
                'name': gettext("left column"),
            },                  
                                
            'col_right': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
                'name': gettext("right column"),
            },
            'extra_context': {
                "plugins": ('TextPlugin',),
                "extra_context": {"width": 250},
                "name": "extra context",
            }
        },
        
        CMS_SOFTROOT = True,
        CMS_MODERATOR = True,
        CMS_PERMISSION = True,
        CMS_REDIRECTS = True,
        CMS_SEO_FIELDS = True,
        CMS_FLAT_URLS = False,
        CMS_MENU_TITLE_OVERWRITE = True,
        CMS_HIDE_UNTRANSLATED = False,
        CMS_URL_OVERWRITE = True,
        
        CMS_PLUGIN_PROCESSORS = tuple(),
        
        CMS_PLUGIN_CONTEXT_PROCESSORS = tuple(),
        
        SOUTH_TESTS_MIGRATE = False,
        
        CMS_NAVIGATION_EXTENDERS = (
            ('cms.test.project.sampleapp.menu_extender.get_nodes', 'SampleApp Menu'),
        ),
            
        TEST_RUNNER = 'cms.test.project.testrunner.CMSTestSuiteRunner',
        JUNIT_OUTPUT_DIR = JUNIT_OUTPUT_DIR
    )
    
    from cms.conf import patch_settings
    patch_settings()
    return test_args, test_labels, failfast, settings

def run_tests(*test_args):
    
    test_args, test_labels, failfast, settings = configure_settings(True, test_args)
    
    from django.test.utils import get_runner 
                   
    failures = get_runner(settings)(verbosity=1, interactive=True, failfast=failfast).run_tests(test_labels)
    sys.exit(failures)

if __name__ == '__main__':
    run_tests(*sys.argv[1:])
