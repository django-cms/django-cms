import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Secret Key (Change this to a secure key for production)
SECRET_KEY = "your-secret-key"

# Debug mode (Set to False in production)
DEBUG = True

# Allowed hosts (Modify as needed for production)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Installed Applications (Includes Django CMS and required dependencies)
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # Required for django CMS
    "cms",  # django CMS Core
    "menus",  # Required for navigation
    "treebeard",  # CMS page structure
    "sekizai",  # Template handling
    "tests",  # Test cases
]

# Middleware (Includes all required Django CMS middleware)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URL Configuration
ROOT_URLCONF = "cms.urls"

# Template Configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],  # Template directory
        "APP_DIRS": True,  # Allow templates from installed apps
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",  # Required for django CMS
                "cms.context_processors.cms_settings",  # Required for django CMS
            ],
        },
    }
]

# WSGI Application
WSGI_APPLICATION = "cms.wsgi.application"

# Database Configuration (Using SQLite for local development)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Language and Timezone Settings
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static Files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media Files (User uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Site Framework (Required for django CMS)
SITE_ID = 1