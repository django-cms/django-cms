#!/usr/bin/env python
import os
import sys
import tempfile
import warnings

import dj_database_url

from cms.exceptions import DontUsePageAttributeWarning


def gettext(s):
    return s


warnings.filterwarnings("ignore", category=DontUsePageAttributeWarning)

permission = True
port = 8000

for arg in sys.argv:
    if arg == '--CMS_PERMISSION=False':
        permission = False

    if arg.startswith('--port='):
        port = int(arg.split('=')[1])


class TempDirs:
    """Simple context manager for temporary directories."""

    def __init__(self, number=3):
        self.number = number

    def __enter__(self):
        self.temp_dirs = [tempfile.mkdtemp() for _ in range(self.number)]
        return self.temp_dirs

    def __exit__(self, *args):
        import shutil
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def main(argv, **full_settings):
    from django.conf import settings
    from django.core.management import execute_from_command_line

    settings.configure(**full_settings)

    # Run migrations
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])

    # Create superuser
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
        print("Created admin user: admin/admin")

    # Create normal user with permissions
    if not User.objects.filter(username='normal').exists():
        normal_user = User.objects.create_user('normal', 'normal@normal.com', 'normal')
        normal_user.is_staff = True
        normal_user.save()

        # Add view_page permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        try:
            from cms.models import Page
            content_type = ContentType.objects.get_for_model(Page)
            perm, created = Permission.objects.get_or_create(
                codename='view_page',
                content_type=content_type,
                defaults={'name': 'Can view page'}
            )
            normal_user.user_permissions.add(perm)
        except Exception as e:
            print(f"Could not add view_page permission: {e}")

        print("Created normal user: normal/normal")

    # Start server
    execute_from_command_line(['manage.py', 'runserver', f'0.0.0.0:{port}', '--noreload'])


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", f"localhost:{port}")
    PROJECT_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "cms", "test_utils")
    )

    PLUGIN_APPS = [
        "djangocms_text",
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
        "djangocms_text": None,
    }

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

    with TempDirs(3) as (media_dir, static_dir, cms_media_dir):
        main(
            sys.argv,
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
            USE_TZ=False,
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
            ALLOWED_HOSTS=['0.0.0.0', 'localhost', '127.0.0.1'],
            LANGUAGE_CODE="en",
            LANGUAGES=(
                ("en", gettext("English")),
                ("de", gettext("German")),
                ("it", gettext("Italian")),
                ("zh-cn", gettext("Chinese (Simplified)")),
            ),
            CMS_LANGUAGES={
                1: [
                    {
                        "code": "en",
                        "name": gettext("English"),
                        "fallbacks": ["de"],
                        "public": True,
                    },
                    {
                        "code": "de",
                        "name": gettext("German"),
                        "fallbacks": ["en"],
                        "public": True,
                    },
                    {
                        "code": "it",
                        "name": gettext("Italian"),
                        "fallbacks": ["en"],
                        "public": True,
                    },
                    {
                        "code": "zh-cn",
                        "name": gettext("Chinese (Simplified)"),
                        "fallbacks": ["en"],
                        "public": True,
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
                "col_left": {
                    "plugins": (
                        "TextPlugin",
                        "LinkPlugin",
                        "MultiColumnPlugin",
                        "StylePlugin",
                    ),
                    "name": gettext("left column"),
                },
                "col_right": {
                    "plugins": (
                        "TextPlugin",
                        "LinkPlugin",
                        "MultiColumnPlugin",
                        "StylePlugin",
                    ),
                    "name": gettext("right column"),
                },
            },
            INSTALLED_APPS=INSTALLED_APPS,
            TEMPLATES=[
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
            DATABASES={
                "default": dj_database_url.config(default="sqlite:///testdb.sqlite")
            },
            MIDDLEWARE=MIDDLEWARES,
            CMS_PERMISSION=permission,
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
            ROOT_URLCONF="cms.test_utils.project.urls",
            PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
            TEST_RUNNER="django.test.runner.DiscoverRunner",
            MIGRATION_MODULES=MIGRATION_MODULES,
            X_FRAME_OPTIONS="SAMEORIGIN",
            CMS_CONFIRM_VERSION4=True,
            TEXT_INLINE_EDITING=False,
        )
