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
    'aldryn-devsync',
    'aldryn-newsblog',
    'divio-styleguide',
    'djangocms-bootstrap4',
    'djangocms-history',
    'djangocms-icon',
    'djangocms-link',
    'djangocms-modules',
    'djangocms-picture',
    'djangocms-snippet',
    'djangocms-style',
    'djangocms-text-ckeditor',
    'djangocms-transfer',
    'djangocms-video',
    'django-filer',
    # </INSTALLED_ADDONS>
]

import aldryn_addons.settings
aldryn_addons.settings.load(locals())


# all django settings can be altered here

INSTALLED_APPS.extend([
    # add your project specific apps here
])

MIDDLEWARE_CLASSES.extend([
    # add your own middlewares here
])

if STAGE in {'local', 'test'}:
    CMS_PAGE_CACHE = False
    CMS_PLACEHOLDER_CACHE = False
    CMS_CACHE_DURATIONS = {
        'menus': 0,
        'content': 0,
        'permissions': 0,
    }

with open('static/iconset.json') as fh:
    ICONSET = fh.read()

ALDRYN_BOOTSTRAP3_ICONSETS = (
    (ICONSET, 'divio', 'Divio icons'),
)

