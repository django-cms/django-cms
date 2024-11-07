#!/usr/bin/env python
import argparse
import os
import sys
import tempfile
import warnings

import dj_database_url

from cms.exceptions import DontUsePageAttributeWarning
from cms.utils.conf import default
from docs.django_settings import SECRET_KEY

gettext = lambda s: s
warnings.filterwarnings("ignore", category=DontUsePageAttributeWarning)


def install_auth_user_model(settings, value):
    if value is None:
        return
    custom_user_app = "cms.test_utils.project." + value.split(".")[0]
    settings["INSTALLED_APPS"].insert(
        settings["INSTALLED_APPS"].index("cms"), custom_user_app
    )
    settings["AUTH_USER_MODEL"] = value


class TempDirs:
    """Simple context manager for temporary directories."""

    def __init__(self, number=3):
        self.number = 3

    def __enter__(self):
        self.temp_dirs = [tempfile.mkdtemp() for _ in range(self.number)]
        return self.temp_dirs

    def __exit__(self, *args):
        for temp_dir in self.temp_dirs:
            os.rmdir(temp_dir)


def main(argv: list[str], **full_settings):
    from django.core.management import execute_from_command_line
    from django.conf import settings

    local_commands = [
        "test",
        "migrate",
        "makemigrations",
    ]

    if (
        len(argv) - sum((arg.startswith("-") for arg in argv[2:]), start=0) < 3
        and argv[1] in local_commands
    ):
        argv.append("cms")
        argv.append("menus")
    settings.configure(**full_settings)
    execute_from_command_line(argv)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", "localhost:8000-9000")
    PROJECT_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "cms", "test_utils")
    )

    PLUGIN_APPS = [
        "djangocms_text_ckeditor",
        "cms.test_utils.project.sampleapp",
        "cms.test_utils.project.placeholderapp",
        "cms.test_utils.project.pluginapp.plugins.link",
        "cms.test_utils.project.pluginapp.plugins.multicolumn",
        "cms.test_utils.project.pluginapp.plugins.multiwrap",
        "cms.test_utils.project.pluginapp.plugins.no_custom_model",
        "cms.test_utils.project.pluginapp.plugins.style",
        "cms.test_utils.project.pluginapp.plugins.manytomany_rel",
        "cms.test_utils.project.pluginapp.plugins.extra_context",
        "cms.test_utils.project.pluginapp.plugins.meta",
        "cms.test_utils.project.pluginapp.plugins.one_thing",
        "cms.test_utils.project.pluginapp.plugins.revdesc",
        "cms.test_utils.project.fakemlng",
        "cms.test_utils.project.objectpermissionsapp",
        "cms.test_utils.project.bunch_of_plugins",
        "cms.test_utils.project.extensionapp",
        "cms.test_utils.project.mti_pluginapp",
        "cms.test_utils.project.nested_plugins_app",
        "cms.test_utils.project.placeholder_relation_field_app",
    ]

    INSTALLED_APPS = [
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "djangocms_admin_style",
        "django.contrib.admin",
        "django.contrib.sites",
        "django.contrib.staticfiles",
        "django.contrib.messages",
        "treebeard",
        "cms",
        "menus",
        "sekizai",
    ] + PLUGIN_APPS

    MIGRATION_MODULES = {
        "auth": None,
        "admin": None,
        "contenttypes": None,
        "sessions": None,
        "sites": None,
        "cms": None,
        "menus": None,
        "djangocms_text_ckeditor": None,
    }

    dynamic_configs = {
        "INSTALLED_APPS": INSTALLED_APPS,
        "TEMPLATES": [
            {
                "NAME": "django",
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [
                    os.path.abspath(os.path.join(PROJECT_PATH, "project", "templates"))
                ],
                "OPTIONS": {
                    "debug": True,
                    "context_processors": [
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                        "django.template.context_processors.i18n",
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.template.context_processors.media",
                        "django.template.context_processors.csrf",
                        "cms.context_processors.cms_settings",
                        "sekizai.context_processors.sekizai",
                        "django.template.context_processors.static",
                    ],
                    "loaders": (
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ),
                },
            }
        ],
        "DATABASES": {
            "default": dj_database_url.config(default="sqlite://localhost/local.sqlite")
        },
    }

    if "test" in sys.argv:
        SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    else:
        SESSION_ENGINE = "django.contrib.sessions.backends.db"

    MIDDLEWARES = [
        "django.middleware.cache.UpdateCacheMiddleware",
        "django.middleware.http.ConditionalGetMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "cms.middleware.language.LanguageCookieMiddleware",
        "cms.middleware.user.CurrentUserMiddleware",
        "cms.middleware.page.CurrentPageMiddleware",
        "cms.middleware.toolbar.ToolbarMiddleware",
        "django.middleware.cache.FetchFromCacheMiddleware",
    ]
    dynamic_configs["MIDDLEWARE"] = MIDDLEWARES

    # Take CMS arguments
    argv = sys.argv
    if "--auth-user-model" in argv:
        pos = argv.index("--auth-user-model")
        if len(argv) > pos + 1:
            install_auth_user_model(dynamic_configs, argv[pos + 1])
            argv.pop(pos)
            argv.pop(pos)
        else:
            raise ValueError("No value provided for --auth-user-model")

    if "--db-url" in argv:
        pos = argv.index("--db-url")
        if len(argv) > pos + 1:
            dynamic_configs["DATABASES"] = {
                "default": dj_database_url.parse(argv[pos + 1])
            }
            argv.pop(pos)
            argv.pop(pos)
        else:
            raise ValueError("No value provided for db-url")

    if "--use-tz" in argv:
        dynamic_configs["USE_TZ"] = True
        argv.pop(argv.index("--use-tz"))
    else:
        dynamic_configs["USE_TZ"] = False

    with TempDirs(3) as (media_dir, static_dir, cms_media_dir):
        main(
            argv,
            PROJECT_PATH=PROJECT_PATH,
            SECRET_KEY="Welcome to django CMS",
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                }
            },
            SESSION_ENGINE=SESSION_ENGINE,
            DEBUG=True,
            DATABASE_SUPPORTS_TRANSACTIONS=True,
            TIME_ZONE="UTC",
            SITE_ID=1,
            USE_I18N=True,
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            MEDIA_ROOT=media_dir,
            STATIC_ROOT=static_dir,
            CMS_MEDIA_ROOT=cms_media_dir,
            CMS_MEDIA_URL="/cms-media/",
            MEDIA_URL="/media/",
            STATIC_URL="/static/",
            ADMIN_MEDIA_PREFIX="/static/admin/",
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            PLUGIN_APPS=PLUGIN_APPS,
            DEBUG_TOOLBAR_PATCH_SETTINGS=False,
            INTERNAL_IPS=["127.0.0.1"],
            AUTHENTICATION_BACKENDS=(
                "django.contrib.auth.backends.ModelBackend",
                "cms.test_utils.project.objectpermissionsapp.backends.ObjectPermissionBackend",
            ),
            LANGUAGE_CODE="en",
            LANGUAGES=(
                ("en", gettext("English")),
                ("fr", gettext("French")),
                ("de", gettext("German")),
                ("pt-br", gettext("Brazilian Portuguese")),
                ("nl", gettext("Dutch")),
                ("es-mx", "Español"),
            ),
            CMS_LANGUAGES={
                1: [
                    {
                        "code": "en",
                        "name": gettext("English"),
                        "fallbacks": ["fr", "de"],
                        "public": True,
                    },
                    {
                        "code": "de",
                        "name": gettext("German"),
                        "fallbacks": ["fr", "en"],
                        "public": True,
                    },
                    {
                        "code": "fr",
                        "name": gettext("French"),
                        "public": True,
                    },
                    {
                        "code": "pt-br",
                        "name": gettext("Brazilian Portuguese"),
                        "public": False,
                    },
                    {
                        "code": "es-mx",
                        "name": "Español",
                        "public": True,
                    },
                ],
                2: [
                    {
                        "code": "de",
                        "name": gettext("German"),
                        "fallbacks": ["fr"],
                        "public": True,
                    },
                    {
                        "code": "fr",
                        "name": gettext("French"),
                        "public": True,
                    },
                ],
                3: [
                    {
                        "code": "nl",
                        "name": gettext("Dutch"),
                        "fallbacks": ["de"],
                        "public": True,
                    },
                    {
                        "code": "de",
                        "name": gettext("German"),
                        "fallbacks": ["nl"],
                        "public": False,
                    },
                ],
                "default": {
                    "hide_untranslated": False,
                },
            },
            CMS_TEMPLATES=(
                ("col_two.html", gettext("two columns")),
                ("col_three.html", gettext("three columns")),
                ("nav_playground.html", gettext("navigation examples")),
                ("simple.html", "simple"),
                ("static.html", "static placeholders"),
            ),
            CMS_PLACEHOLDER_CONF={
                "col_sidebar": {
                    "plugins": (
                        "FilePlugin",
                        "LinkPlugin",
                        "PicturePlugin",
                        "TextPlugin",
                        "SnippetPlugin",
                    ),
                    "name": gettext("sidebar column"),
                },
                "col_left": {
                    "plugins": (
                        "FilePlugin",
                        "LinkPlugin",
                        "PicturePlugin",
                        "TextPlugin",
                        "SnippetPlugin",
                        "GoogleMapPlugin",
                        "MultiColumnPlugin",
                        "StylePlugin",
                    ),
                    "name": gettext("left column"),
                    "plugin_modules": {"LinkPlugin": "Different Grouper"},
                    "plugin_labels": {"LinkPlugin": gettext("Add a link")},
                },
                "col_right": {
                    "plugins": (
                        "FilePlugin",
                        "LinkPlugin",
                        "PicturePlugin",
                        "TextPlugin",
                        "SnippetPlugin",
                        "GoogleMapPlugin",
                        "MultiColumnPlugin",
                        "StylePlugin",
                    ),
                    "name": gettext("right column"),
                },
                "extra_context": {
                    "plugins": ("TextPlugin",),
                    "extra_context": {"width": 250},
                    "name": "extra context",
                },
            },
            CMS_PERMISSION=True,
            CMS_PUBLIC_FOR="all",
            CMS_CACHE_DURATIONS={
                "menus": 60,
                "content": 60,
                "permissions": 60,
            },
            CMS_APPHOOKS=[],
            CMS_PLUGIN_PROCESSORS=(),
            CMS_PLUGIN_CONTEXT_PROCESSORS=(),
            CMS_SITE_CHOICES_CACHE_KEY="CMS:site_choices",
            CMS_PAGE_CHOICES_CACHE_KEY="CMS:page_choices",
            CMS_NAVIGATION_EXTENDERS=[
                (
                    "cms.test_utils.project.sampleapp.menu_extender.get_nodes",
                    "SampleApp Menu",
                ),
            ],
            ROOT_URLCONF="cms.test_utils.project.urls",
            PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
            ALLOWED_HOSTS=["localhost"],
            TEST_RUNNER="django.test.runner.DiscoverRunner",
            MIGRATION_MODULES=MIGRATION_MODULES,
            X_FRAME_OPTIONS="SAMEORIGIN",
            CMS_CONFIRM_VERSION4=True,
            **dynamic_configs,
        )
