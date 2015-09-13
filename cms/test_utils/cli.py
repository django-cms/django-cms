# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import dj_database_url

import django
from django.utils import six

from cms.utils.compat import DJANGO_1_6, DJANGO_1_7

gettext = lambda s: s

urlpatterns = []


def _detect_migration_layout(apps):
    SOUTH_MODULES = {}
    DJANGO_MODULES = {}

    for module in apps:
        try:
            __import__('%s.migrations_django' % module)
            DJANGO_MODULES[module] = '%s.migrations_django' % module
            SOUTH_MODULES[module] = '%s.migrations' % module
        except Exception:
            pass
    return DJANGO_MODULES, SOUTH_MODULES


def configure(db_url, **extra):
    from django.conf import settings
    if six.PY3:
        siteid = 1
    else:
        siteid = long(1)  # nopyflakes

    os.environ['DJANGO_SETTINGS_MODULE'] = 'cms.test_utils.cli'
    if not 'DATABASES' in extra:
        DB = dj_database_url.parse(db_url)
    else:
        DB = {}
    PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
    defaults = dict(
        PROJECT_PATH=PROJECT_PATH,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True,
        DEBUG=True,
        TEMPLATE_DEBUG=True,
        DATABASE_SUPPORTS_TRANSACTIONS=True,
        DATABASES={
            'default': DB
        },
        SITE_ID=siteid,
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
        MIDDLEWARE_CLASSES=[
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.http.ConditionalGetMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.BrokenLinkEmailsMiddleware',
            'django.middleware.common.CommonMiddleware',
            'cms.middleware.language.LanguageCookieMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
        ],
        INSTALLED_APPS=[
            'debug_toolbar',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'djangocms_admin_style',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'django.contrib.messages',
            'treebeard',
            'cms',
            'menus',
            'djangocms_text_ckeditor',
            'djangocms_column',
            'djangocms_picture',
            'djangocms_file',
            'djangocms_flash',
            'djangocms_googlemap',
            'djangocms_teaser',
            'djangocms_video',
            'djangocms_inherit',
            'djangocms_style',
            'djangocms_link',
            'cms.test_utils.project.sampleapp',
            'cms.test_utils.project.placeholderapp',
            'cms.test_utils.project.pluginapp.plugins.manytomany_rel',
            'cms.test_utils.project.pluginapp.plugins.extra_context',
            'cms.test_utils.project.pluginapp.plugins.meta',
            'cms.test_utils.project.pluginapp.plugins.one_thing',
            'cms.test_utils.project.fakemlng',
            'cms.test_utils.project.fileapp',
            'cms.test_utils.project.objectpermissionsapp',
            'cms.test_utils.project.bunch_of_plugins',
            'cms.test_utils.project.extensionapp',
            'cms.test_utils.project.mti_pluginapp',
            'reversion',
            'sekizai',
            'hvad',
        ],
        DEBUG_TOOLBAR_PATCH_SETTINGS = False,
        INTERNAL_IPS = ['127.0.0.1'],
        AUTHENTICATION_BACKENDS=(
            'django.contrib.auth.backends.ModelBackend',
            'cms.test_utils.project.objectpermissionsapp.backends.ObjectPermissionBackend',
        ),
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
                    'code': 'en',
                    'name': gettext('English'),
                    'fallbacks': ['fr', 'de'],
                    'public': True,
                },
                {
                    'code': 'de',
                    'name': gettext('German'),
                    'fallbacks': ['fr', 'en'],
                    'public': True,
                },
                {
                    'code': 'fr',
                    'name': gettext('French'),
                    'public': True,
                },
                {
                    'code': 'pt-br',
                    'name': gettext('Brazilian Portuguese'),
                    'public': False,
                },
                {
                    'code': 'es-mx',
                    'name': u'Español',
                    'public': True,
                },
            ],
            2: [
                {
                    'code': 'de',
                    'name': gettext('German'),
                    'fallbacks': ['fr'],
                    'public': True,
                },
                {
                    'code': 'fr',
                    'name': gettext('French'),
                    'public': True,
                },
            ],
            3: [
                {
                    'code': 'nl',
                    'name': gettext('Dutch'),
                    'fallbacks': ['de'],
                    'public': True,
                },
                {
                    'code': 'de',
                    'name': gettext('German'),
                    'fallbacks': ['nl'],
                    'public': False,
                },
            ],
            'default': {
                'hide_untranslated': False,
            },
        },
        CMS_TEMPLATES=(
            ('col_two.html', gettext('two columns')),
            ('col_three.html', gettext('three columns')),
            ('nav_playground.html', gettext('navigation examples')),
            ('simple.html', 'simple'),
            ('static.html', 'static placeholders'),
        ),
        CMS_PLACEHOLDER_CONF={
            'col_sidebar': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'MultiColumnPlugin', 'SnippetPlugin'),
                'name': gettext("sidebar column")
            },
            'col_left': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin', 'GoogleMapPlugin',
                            'MultiColumnPlugin', 'StylePlugin', 'EmptyPlugin'),
                'name': gettext("left column"),
                'plugin_modules': {
                    'LinkPlugin': 'Different Grouper'
                },
                'plugin_labels': {
                    'LinkPlugin': gettext('Add a link')
                },
            },
            'col_right': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                            'TextPlugin', 'SnippetPlugin', 'GoogleMapPlugin', 'MultiColumnPlugin',
                            'StylePlugin'),
                'name': gettext("right column")
            },
            'extra_context': {
                "plugins": ('TextPlugin',),
                "extra_context": {"extra_width": 250},
                "name": "extra context"
            },
        },
        CMS_PERMISSION=True,
        CMS_PUBLIC_FOR='all',
        CMS_CACHE_DURATIONS={
            'menus': 0,
            'content': 0,
            'permissions': 0,
        },
        CMS_APPHOOKS=[],
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
        ),
        ALLOWED_HOSTS=['localhost'],
    )
    from django.utils.functional import empty
    settings._wrapped = empty
    defaults.update(extra)

    if DJANGO_1_7:
        defaults.update(dict(
            TEMPLATE_CONTEXT_PROCESSORS=[
                "django.contrib.auth.context_processors.auth",
                'django.contrib.messages.context_processors.messages',
                "django.core.context_processors.i18n",
                "django.core.context_processors.debug",
                "django.core.context_processors.request",
                "django.core.context_processors.media",
                'django.core.context_processors.csrf',
                "cms.context_processors.cms_settings",
                "sekizai.context_processors.sekizai",
                "django.core.context_processors.static",
            ],
            TEMPLATE_LOADERS=(
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader',
            ),
            TEMPLATE_DIRS=[
                os.path.abspath(os.path.join(PROJECT_PATH, 'project', 'templates'))
            ],
        ))
    else:
        defaults['TEMPLATES'] = [
            {
                'NAME': 'django',
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'DIRS': [os.path.abspath(os.path.join(PROJECT_PATH, 'project', 'templates'))],
                'OPTIONS': {
                    'context_processors': [
                        "django.contrib.auth.context_processors.auth",
                        'django.contrib.messages.context_processors.messages',
                        "django.template.context_processors.i18n",
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.template.context_processors.media",
                        'django.template.context_processors.csrf',
                        "cms.context_processors.cms_settings",
                        "sekizai.context_processors.sekizai",
                        "django.template.context_processors.static",
                    ],
                }
            }
        ]

    plugins = ('djangocms_column', 'djangocms_file', 'djangocms_flash', 'djangocms_googlemap',
               'djangocms_inherit', 'djangocms_link', 'djangocms_picture', 'djangocms_style',
               'djangocms_teaser', 'djangocms_video')

    DJANGO_MIGRATION_MODULES, SOUTH_MIGRATION_MODULES = _detect_migration_layout(plugins)

    if DJANGO_1_6:
        defaults['INSTALLED_APPS'].append('south')
        defaults['SOUTH_MIGRATION_MODULES'] = SOUTH_MIGRATION_MODULES
    else:
        defaults['MIGRATION_MODULES'] = DJANGO_MIGRATION_MODULES
        if not defaults.get('TESTS_MIGRATE', False):
            # Disable migrations for Django 1.7+
            class DisableMigrations(object):

                def __contains__(self, item):
                    return True

                def __getitem__(self, item):
                    return "notmigrations"

            defaults['MIGRATION_MODULES'] = DisableMigrations()

    if 'AUTH_USER_MODEL' in extra:
        custom_user_app = 'cms.test_utils.project.' + extra['AUTH_USER_MODEL'].split('.')[0]
        defaults['INSTALLED_APPS'].insert(defaults['INSTALLED_APPS'].index('cms'), custom_user_app)

    # add data from env
    extra_settings = os.environ.get("DJANGO_EXTRA_SETTINGS", None)

    if extra_settings:
        from json import load, loads

        if os.path.exists(extra_settings):
            with open(extra_settings) as fobj:
                defaults.update(load(fobj))
        else:
            defaults.update(loads(extra_settings))

    settings.configure(**defaults)
    if DJANGO_1_6:
        from south.management.commands import patch_for_test_db_setup

        patch_for_test_db_setup()
        from django.contrib import admin

        admin.autodiscover()
    else:
        django.setup()
