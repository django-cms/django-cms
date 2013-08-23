# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import dj_database_url

gettext = lambda s: s

urlpatterns = []

def configure(db_url, **extra):
    from django.conf import settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cms.test_utils.cli'
    if not 'DATABASES' in extra:
        DB = dj_database_url.parse(db_url)
    else:
        DB = {}
    defaults = dict(
        CACHE_BACKEND='locmem:///',
        DEBUG=True,
        TEMPLATE_DEBUG=True,
        DATABASE_SUPPORTS_TRANSACTIONS=True,
        DATABASES={
            'default': DB
        },
        SITE_ID=1,
        USE_I18N=True,
        MEDIA_ROOT='/media/',
        STATIC_ROOT='/static/',
        CMS_MEDIA_ROOT='/cms-media/',
        CMS_MEDIA_URL='/cms-media/',
        MEDIA_URL='/media/',
        STATIC_URL='/static/',
        ADMIN_MEDIA_PREFIX='/static/admin/',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        SECRET_KEY='key',
        TEMPLATE_LOADERS=(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.eggs.Loader',
        ),
        TEMPLATE_CONTEXT_PROCESSORS=[
            "django.contrib.auth.context_processors.auth",
            'django.contrib.messages.context_processors.messages',
            "django.core.context_processors.i18n",
            "django.core.context_processors.debug",
            "django.core.context_processors.request",
            "django.core.context_processors.media",
            'django.core.context_processors.csrf',
            "cms.context_processors.media",
            "sekizai.context_processors.sekizai",
            "django.core.context_processors.static",
        ],
        TEMPLATE_DIRS=[
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'project', 'templates'))
        ],
        MIDDLEWARE_CLASSES=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.doc.XViewMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.transaction.TransactionMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
            'cms.middleware.language.LanguageCookieMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
        ],
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'django.contrib.messages',
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
            'cms.test_utils.project.pluginapp.plugins.extra_context',
            'cms.test_utils.project.fakemlng',
            'cms.test_utils.project.fileapp',
            'south',
            'reversion',
            'sekizai',
            'hvad',
        ],
        LANGUAGE_CODE="en",
        LANGUAGES=(
            ('en', gettext('English')),
            ('fr', gettext('French')),
            ('de', gettext('German')),
            ('pt-br', gettext('Brazilian Portuguese')),
            ('nl', gettext("Dutch")),
            ('es-mx', u'Español'),
        ),
        CMS_LANGUAGES={
            1: [
                {
                    'code':'en',
                    'name':gettext('English'),
                    'fallbacks':['fr', 'de'],
                    'public':True,
                },
                {
                    'code':'de',
                    'name':gettext('German'),
                    'fallbacks':['fr', 'en'],
                    'public':True,
                },
                {
                    'code':'fr',
                    'name':gettext('French'),
                    'public':True,
                },
                {
                    'code':'pt-br',
                    'name':gettext('Brazilian Portuguese'),
                    'public':False,
                },
                {
                    'code':'es-mx',
                    'name':u'Español',
                    'public':True,
                },
            ],
            2: [
                {
                    'code':'de',
                    'name':gettext('German'),
                    'fallbacks':['fr', 'en'],
                    'public':True,
                },
                {
                    'code':'fr',
                    'name':gettext('French'),
                    'public':True,
                },
            ],
            3: [
                {
                    'code':'nl',
                    'name':gettext('Dutch'),
                    'fallbacks':['fr', 'en'],
                    'public':True,
                },
                {
                    'code':'de',
                    'name':gettext('German'),
                    'fallbacks':['fr', 'en'],
                    'public':False,
                },
            ],
            'default': {
                'hide_untranslated':False,
            },
        },
        CMS_TEMPLATES=(
            ('col_two.html', gettext('two columns')),
            ('col_three.html', gettext('three columns')),
            ('nav_playground.html', gettext('navigation examples')),
        ),
        CMS_PLACEHOLDER_CONF={
            'col_sidebar': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin'),
                'name': gettext("sidebar column")
            },

            'col_left': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin', 'GoogleMapPlugin', 'MultiColumnPlugin'),
                'name': gettext("left column")
            },

            'col_right': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin', 'GoogleMapPlugin', 'MultiColumnPlugin'),
                'name': gettext("right column")
            },
            'extra_context': {
                "plugins": ('TextPlugin',),
                "extra_context": {"width": 250},
                "name": "extra context"
            },
        },
        CMS_SOFTROOT=True,
        CMS_PERMISSION=True,
        CMS_PUBLIC_FOR='all',
        CMS_CACHE_DURATIONS={
            'menus': 0,
            'content': 0,
            'permissions': 0,
        },
        CMS_APPHOOKS=[],
        CMS_REDIRECTS=True,
        CMS_SEO_FIELDS=True,
        CMS_MENU_TITLE_OVERWRITE=True,
        CMS_URL_OVERWRITE=True,
        CMS_SHOW_END_DATE=True,
        CMS_SHOW_START_DATE=True,
        CMS_PLUGIN_PROCESSORS=tuple(),
        CMS_PLUGIN_CONTEXT_PROCESSORS=tuple(),
        CMS_SITE_CHOICES_CACHE_KEY='CMS:site_choices',
        CMS_PAGE_CHOICES_CACHE_KEY='CMS:page_choices',
        SOUTH_TESTS_MIGRATE=False,
        CMS_NAVIGATION_EXTENDERS=(
            ('cms.test_utils.project.sampleapp.menu_extender.get_nodes', 'SampleApp Menu'),
        ),
        TEST_RUNNER='cms.test_utils.runners.NormalTestRunner',
        JUNIT_OUTPUT_DIR='.',
        TIME_TESTS=False,
        ROOT_URLCONF='cms.test_utils.cli',
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        )
    )
    from django.utils.functional import empty
    settings._wrapped = empty
    defaults.update(extra)
    # add data from env
    extra_settings = os.environ.get("DJANGO_EXTRA_SETTINGS", None)
    if extra_settings:
        from django.utils.simplejson import load, loads
        if os.path.exists(extra_settings):
            with open(extra_settings) as fobj:
                defaults.update(load(fobj))
        else:
            defaults.update(loads(extra_settings))
    settings.configure(**defaults)
    from south.management.commands import patch_for_test_db_setup
    patch_for_test_db_setup()
    from django.contrib import admin
    admin.autodiscover()
