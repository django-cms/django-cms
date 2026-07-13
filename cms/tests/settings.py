"""Django settings module for running the django CMS test suite with pytest.

This mirrors the configuration that ``manage.py`` builds dynamically and passes
to ``settings.configure()``. It is exposed as an importable settings module so
that ``pytest`` (via ``pytest-django``) and ``django-admin`` can pick it up
through ``DJANGO_SETTINGS_MODULE=cms.tests.settings``.

Values normally derived from command line arguments in ``manage.py`` can be
overridden through environment variables:

* ``DATABASE_URL``      -- database connection (default: local sqlite file)
* ``AUTH_USER_MODEL``   -- custom auth user model, e.g. ``customuserapp.User``
* ``USE_TZ``            -- set to a truthy value to enable timezone support
"""

import os
import tempfile

import dj_database_url


def gettext(s):
    return s


os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", "localhost:8000-9000")
os.environ.setdefault("DJANGO_TESTS", "1")

PROJECT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "test_utils")
)

# django CMS ships a large number of test-only apps that provide plugins,
# extensions and sample models used throughout the suite.
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

# A custom auth user model may be requested via the AUTH_USER_MODEL env var,
# mirroring manage.py's ``--auth-user-model`` option.
_auth_user_model = os.environ.get("AUTH_USER_MODEL")
if _auth_user_model:
    _custom_user_app = "cms.test_utils.project." + _auth_user_model.split(".")[0]
    INSTALLED_APPS.insert(INSTALLED_APPS.index("cms"), _custom_user_app)
    AUTH_USER_MODEL = _auth_user_model

# Disable migrations for speed; the schema is created directly from the models.
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

TEMPLATES = [
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
]

DATABASES = {
    "default": dj_database_url.config(default="sqlite://localhost/local.sqlite")
}

USE_TZ = bool(os.environ.get("USE_TZ"))

# The session cache backend is used because the test suite relies on it.
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

MIDDLEWARE = [
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

# Temporary directories for media/static roots, cleaned up by the OS.
MEDIA_ROOT = tempfile.mkdtemp(prefix="cms-media-")
STATIC_ROOT = tempfile.mkdtemp(prefix="cms-static-")
CMS_MEDIA_ROOT = tempfile.mkdtemp(prefix="cms-cms-media-")

SECRET_KEY = "Welcome to django CMS"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
DEBUG = True
DATABASE_SUPPORTS_TRANSACTIONS = True
TIME_ZONE = "UTC"
SITE_ID = 1
USE_I18N = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
CMS_MEDIA_URL = "/cms-media/"
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
ADMIN_MEDIA_PREFIX = "/static/admin/"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INTERNAL_IPS = ["127.0.0.1"]
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "cms.test_utils.project.objectpermissionsapp.backends.ObjectPermissionBackend",
)
LANGUAGE_CODE = "en"
LANGUAGES = (
    ("en", gettext("English")),
    ("fr", gettext("French")),
    ("de", gettext("German")),
    ("pt-br", gettext("Brazilian Portuguese")),
    ("nl", gettext("Dutch")),
    ("es-mx", "Español"),
)
CMS_LANGUAGES = {
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
}
CMS_TEMPLATES = (
    ("col_two.html", gettext("two columns")),
    ("col_three.html", gettext("three columns")),
    ("nav_playground.html", gettext("navigation examples")),
    ("simple.html", "simple"),
    ("static.html", "static placeholders"),
)
CMS_PLACEHOLDER_CONF = {
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
}
CMS_PERMISSION = True
CMS_PUBLIC_FOR = "all"
CMS_CACHE_DURATIONS = {
    "menus": 60,
    "content": 60,
    "permissions": 60,
}
CMS_APPHOOKS = []
CMS_PLUGIN_PROCESSORS = ()
CMS_PLUGIN_CONTEXT_PROCESSORS = ()
CMS_SITE_CHOICES_CACHE_KEY = "CMS:site_choices"
CMS_PAGE_CHOICES_CACHE_KEY = "CMS:page_choices"
CMS_NAVIGATION_EXTENDERS = [
    (
        "cms.test_utils.project.sampleapp.menu_extender.get_nodes",
        "SampleApp Menu",
    ),
]
ROOT_URLCONF = "cms.test_utils.project.urls"
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
ALLOWED_HOSTS = ["localhost"]
TEST_RUNNER = "django.test.runner.DiscoverRunner"
X_FRAME_OPTIONS = "SAMEORIGIN"
TEXT_INLINE_EDITING = False  # Do not pollute toolbar for tests
