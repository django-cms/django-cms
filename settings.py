# -*- coding: utf-8 -*-
import os
from django.utils.translation import ugettext_lazy as _
from aldryn_addons.utils import boolean_ish

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
    'aldryn-redirects',
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
    'elasticapm.contrib.django',
    'project',
    'project.banner',
])

MIDDLEWARE_CLASSES.extend([
    # add your own middlewares here
])

# =============================================================================
# Elastic
# =============================================================================
ENABLE_ELASTIC_APM = boolean_ish(env('ENABLE_ELASTIC_APM', True))
if STAGE in {'local', 'test'}:
    ELASTIC_DEBUG = True
else:
    ELASTIC_DEBUG = False

if ENABLE_ELASTIC_APM:
    MIDDLEWARE_CLASSES.insert(
        0, 'elasticapm.contrib.django.middleware.TracingMiddleware')
    ELASTIC_APM = {
        'DEBUG': ELASTIC_DEBUG,
        # Set required service name. Allowed characters:
        # a-z, A-Z, 0-9, -, _, and space
        'SERVICE_NAME': 'divio2018-{}'.format(STAGE),
        # Use if APM Server requires a token
        'SECRET_TOKEN': 'VUYkSeFvuVEElYO5c6',
        # Set custom APM Server URL (default: http://localhost:8200)
        'SERVER_URL': 'https://138eff00f6ed466da742b5c7d106e5e2.apm.us-east-1.aws.cloud.es.io:443',
    }

# =============================================================================
# django CMS
# =============================================================================
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

DJANGOCMS_BOOTSTRAP4_COLOR_STYLE_CHOICES = (
    ('primary', _('Primary')),
    ('secondary', _('Secondary')),
    ('success', _('Success')),
    ('danger', _('Danger')),
    ('warning', _('Warning')),
    ('info', _('Info')),
    ('light', _('Light')),
    ('dark', _('Dark')),
    ('pink', _('Pink')),
    ('purple', _('Purple')),
)

DJANGOCMS_BOOTSTRAP4_CAROUSEL_TEMPLATES = (
    ('default', _('Default')),
    ('iframe', _('Iframe')),
)

DJANGOCMS_BOOTSTRAP4_CAROUSEL_ASPECT_RATIOS = (
    (16, 9),
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
