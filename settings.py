# -*- coding: utf-8 -*-
import os


env = os.getenv
STAGE = env('STAGE', 'local').lower()

INSTALLED_ADDONS = [
    # <INSTALLED_ADDONS>  # Warning: text inside the INSTALLED_ADDONS tags is auto-generated. Manual changes will be overwritten.
    'aldryn-addons',
    'aldryn-django',
    'aldryn-sso',
    'aldryn-django-cms',
    'aldryn-forms',
    'aldryn-newsblog',
    'divio-styleguide',
    'djangocms-bootstrap4',
    'djangocms-file',
    'djangocms-history',
    'djangocms-icon',
    'djangocms-link',
    'django-cms-marketplace',
    'djangocms-modules',
    'djangocms-picture',
    'djangocms-snippet',
    'djangocms-style',
    'djangocms-text-ckeditor',
    'djangocms-transfer',
    'djangocms-video',
    'django-filer',
    'django-privacy-mgmt',
    # </INSTALLED_ADDONS>
]

import aldryn_addons.settings
aldryn_addons.settings.load(locals())


# all django settings can be altered here

INSTALLED_APPS.extend([
    # add your project specific apps here
    'project',
    'project.banner',
])

MIDDLEWARE_CLASSES.extend([
    # add your own middlewares here
])

# without this the access-control-allow-origin iframes won't work
CMS_PAGE_CACHE = False

if STAGE in {'local', 'test'}:
    CMS_PLACEHOLDER_CACHE = False
    CMS_CACHE_DURATIONS = {
        'menus': 0,
        'content': 0,
        'permissions': 0,
    }

with open('static/iconset.json') as fh:
    ICONSET = fh.read()

DJANGOCMS_ICON_SETS = (
    (ICONSET, 'divio', 'Divio icons'),
)

DJANGOCMS_BOOTSTRAP4_SPACER_SIZES = (
    ('0', '* 0'),
    ('1', '* .25'),
    ('2', '* .5'),
    ('3', '* 1'),
    ('4', '* 1.5'),
    ('5', '* 3'),
    ('6', '* 5'),
    ('7', '* 7'),
)

TEXT_HTML_SANITIZE = False


# =============================================================================
# Pandadoc Plugin
# =============================================================================
PANDADOC_CLIENT_ID = env('PANDADOC_CLIENT_ID')
PANDADOC_CLIENT_SECRET = env('PANDADOC_CLIENT_SECRET')
PANDADOC_REDIRECT_URI = env('PANDADOC_REDIRECT_URI')

# =============================================================================
# Google reCAPTCHA
# =============================================================================
RECAPTCHA_SITE_KEY = env('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = env('RECAPTCHA_SECRET_KEY')
