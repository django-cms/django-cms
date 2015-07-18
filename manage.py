# -*- coding: utf-8 -*-
import os

import app_manage

from cms.utils.compat import DJANGO_1_6, DJANGO_1_7

gettext = lambda s: s


if __name__ == '__main__':
    os.environ.setdefault(
        'DJANGO_LIVE_TEST_SERVER_ADDRESS',
        'localhost:8000-9000'
    )
    PROJECT_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'cms', 'test_utils')
    )

    INSTALLED_APPS = [
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
        'better_test',
    ]

    dynamic_configs = {}

    if DJANGO_1_7:
        dynamic_configs.update(dict(
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
        dynamic_configs['TEMPLATES'] = [
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

    if DJANGO_1_6:
        # South overrides the test command, thus insert it before better_test
        INSTALLED_APPS.insert(0, 'south')
        dynamic_configs['SOUTH_MIGRATION_MODULES'] = {
            'cms': 'cms.south_migrations',
            'menus': 'menus.south_migrations',
            'djangocms_column': 'djangocms_column.migrations',
            'djangocms_file': 'djangocms_file.migrations',
            'djangocms_flash': 'djangocms_flash.migrations',
            'djangocms_googlemap': 'djangocms_googlemap.migrations',
            'djangocms_inherit': 'djangocms_inherit.migrations',
            'djangocms_link': 'djangocms_link.migrations',
            'djangocms_picture': 'djangocms_picture.migrations',
            'djangocms_style': 'djangocms_style.migrations',
            'djangocms_teaser': 'djangocms_teaser.migrations',
            'djangocms_text_ckeditor': 'djangocms_text_ckeditor.south_migrations',
            'djangocms_video': 'djangocms_video.migrations',
            'meta': 'cms.test_utils.project.pluginapp.plugins.meta.south_migrations',
            'manytomany_rel': 'cms.test_utils.project.pluginapp.plugins.manytomany_rel.south_migrations',
            'fileapp': 'cms.test_utils.project.fileapp.south_migrations',
            'placeholderapp': 'cms.test_utils.project.placeholderapp.south_migrations',
            'sampleapp': 'cms.test_utils.project.sampleapp.south_migrations',
            'emailuserapp': 'cms.test_utils.project.emailuserapp.south_migrations',
            'customuserapp': 'cms.test_utils.project.customuserapp.south_migrations',
            'fakemlng': 'cms.test_utils.project.fakemlng.south_migrations',
            'extra_context': 'cms.test_utils.project.pluginapp.plugins.extra_context.south_migrations',
            'one_thing': 'cms.test_utils.project.pluginapp.plugins.one_thing.south_migrations',
            'bunch_of_plugins': 'cms.test_utils.project.bunch_of_plugins.south_migrations',
            'extensionapp': 'cms.test_utils.project.extensionapp.south_migrations',
            'objectpermissionsapp': 'cms.test_utils.project.objectpermissionsapp.south_migrations',
            'mti_pluginapp': 'cms.test_utils.project.mti_pluginapp.south_migrations',
        }
    else:
        dynamic_configs['MIGRATION_MODULES'] = {
            'djangocms_column': 'djangocms_column.migrations_django',
            'djangocms_file': 'djangocms_file.migrations_django',
            'djangocms_flash': 'djangocms_flash.migrations_django',
            'djangocms_googlemap': 'djangocms_googlemap.migrations_django',
            'djangocms_inherit': 'djangocms_inherit.migrations_django',
            'djangocms_link': 'djangocms_link.migrations_django',
            'djangocms_picture': 'djangocms_picture.migrations_django',
            'djangocms_style': 'djangocms_style.migrations_django',
            'djangocms_teaser': 'djangocms_teaser.migrations_django',
            'djangocms_video': 'djangocms_video.migrations_django',
            'meta': 'cms.test_utils.project.pluginapp.plugins.meta.migrations',
            'manytomany_rel': 'cms.test_utils.project.pluginapp.plugins.manytomany_rel.migrations',
            'fileapp': 'cms.test_utils.project.fileapp.migrations',
            'placeholderapp': 'cms.test_utils.project.placeholderapp.migrations',
            'sampleapp': 'cms.test_utils.project.sampleapp.migrations',
            'emailuserapp': 'cms.test_utils.project.emailuserapp.migrations',
            'fakemlng': 'cms.test_utils.project.fakemlng.migrations',
            'extra_context': 'cms.test_utils.project.pluginapp.plugins.extra_context.migrations',
            'one_thing': 'cms.test_utils.project.pluginapp.plugins.one_thing.migrations',
            'bunch_of_plugins': 'cms.test_utils.project.bunch_of_plugins.migrations',
            'extensionapp': 'cms.test_utils.project.extensionapp.migrations',
            'objectpermissionsapp': 'cms.test_utils.project.objectpermissionsapp.migrations',
            'mti_pluginapp': 'cms.test_utils.project.mti_pluginapp.migrations',
        }

    app_manage.main(
        ['cms', 'menus'],
        PROJECT_PATH=PROJECT_PATH,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        SESSION_ENGINE="django.contrib.sessions.backends.cache",
        CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True,
        DEBUG=True,
        TEMPLATE_DEBUG=True,
        DATABASE_SUPPORTS_TRANSACTIONS=True,
        DATABASES=app_manage.DatabaseConfig(
            env='DATABASE_URL',
            arg='--db-url',
            default='sqlite://localhost/local.sqlite'
        ),
        USE_TZ=app_manage.Config(
            env='USE_TZ',
            arg=app_manage.Flag('--use-tz'),
            default=False,
        ),
        SITE_ID=1,
        USE_I18N=True,
        MEDIA_ROOT=app_manage.TempDir(),
        STATIC_ROOT=app_manage.TempDir(),
        CMS_MEDIA_ROOT=app_manage.TempDir(),
        CMS_MEDIA_URL='/cms-media/',
        MEDIA_URL='/media/',
        STATIC_URL='/static/',
        ADMIN_MEDIA_PREFIX='/static/admin/',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        MIDDLEWARE_CLASSES=[
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.http.ConditionalGetMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'cms.middleware.language.LanguageCookieMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
        ],
        INSTALLED_APPS=INSTALLED_APPS,
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
                'TextPlugin', 'SnippetPlugin'),
                'name': gettext("sidebar column")
            },
            'col_left': {
                'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin',
                'TextPlugin', 'SnippetPlugin', 'GoogleMapPlugin', 'MultiColumnPlugin', 'StylePlugin'),
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
                'TextPlugin', 'SnippetPlugin', 'GoogleMapPlugin', 'MultiColumnPlugin', 'StylePlugin'),
                'name': gettext("right column")
            },
            'extra_context': {
                "plugins": ('TextPlugin',),
                "extra_context": {"width": 250},
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
        CMS_PLUGIN_PROCESSORS=(),
        CMS_PLUGIN_CONTEXT_PROCESSORS=(),
        CMS_SITE_CHOICES_CACHE_KEY='CMS:site_choices',
        CMS_PAGE_CHOICES_CACHE_KEY='CMS:page_choices',
        SOUTH_TESTS_MIGRATE=False,
        CMS_NAVIGATION_EXTENDERS=[
            ('cms.test_utils.project.sampleapp.menu_extender.get_nodes',
             'SampleApp Menu'),
        ],
        ROOT_URLCONF='cms.test_utils.project.urls',
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ),
        ALLOWED_HOSTS=['localhost'],
        TEST_RUNNER='django.test.runner.DiscoverRunner',
        **dynamic_configs
    )
