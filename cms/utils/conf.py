# -*- coding: utf-8 -*-
from functools import update_wrapper
import urlparse
from cms import constants
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import os


def default(name):
    def decorator(wrapped):
        def wrapper():
            if hasattr(settings, name):
                return getattr(settings, name)
            return wrapped()
        update_wrapper(wrapper, wrapped)
        return wrapped
    return decorator


DEFAULTS = {
    'TEMPLATE_INHERITANCE': True,
    'PLACEHOLDER_CONF': {},
    'PERMISSION': False,
    'PUBLIC_FOR': 'all',
    'CONTENT_CACHE_DURATION': 60,
    'SHOW_START_DATE': False,
    'SHOW_END_DATE': False,
    'URL_OVERWRITE': True,
    'MENU_TITLE_OVERWRITE': False,
    'REDIRECTS': False,
    'SEO_FIELDS': False,
    'APPHOOKS': [],
    'SOFTROOT': False,
    'SITE_CHOICES_CACHE_KEY': 'CMS:site_choices',
    'PAGE_CHOICES_CACHE_KEY': 'CMS:page_choices',
    'MEDIA_PATH': 'cms/',
    'PAGE_MEDIA_PATH': 'cms_page_media/',
    'TITLE_CHARACTER': '+',
    'CACHE_PREFIX': 'cms-',
    'PLUGIN_PROCESSORS': [],
    'PLUGIN_CONTEXT_PROCESSORS': []
}

def get_cache_durations():
    return {
        'menus': getattr(settings, 'MENU_CACHE_DURATION', 60 * 60),
        'content': get_setting('CONTENT_CACHE_DURATION'),
        'permissions': 60 * 60,
    }

@default('CMS_MEDIA_ROOT')
def get_media_root():
    return os.path.join(settings.MEDIA_ROOT, get_setting('MEDIA_PATH'))

@default('CMS_MEDIA_ROOT')
def get_media_url():
    return urlparse.urljoin(settings.MEDIA_URL, get_setting('MEDIA_PATH'))

@default('PLACEHOLDER_FRONTEND_EDITING')
def get_placeholder_frontend_editing():
    return True

def get_templates():
    templates = list(getattr(settings, 'CMS_TEMPLATES', []))
    if get_setting('TEMPLATE_INHERITANCE'):
        templates.append((constants.TEMPLATE_INHERITANCE_MAGIC, _('Inherit the template of the nearest ancestor')))
    return templates

def get_languages():
    languages = getattr(settings, 'CMS_LANGUAGES', None)
    if languages:
        return languages
    else:
        return {
            settings.SITE_ID: [{'code': code, 'name': _(name)} for code, name in settings.LANGUAGES]
        }

COMPLEX = {
    'CACHE_DURATIONS': get_cache_durations,
    'MEDIA_ROOT': get_media_root,
    'MEDIA_URL': get_media_url,
    # complex because not prefixed by CMS_
    'PLACEHOLDER_FRONTEND_EDITING': get_placeholder_frontend_editing,
    'TEMPLATES': get_templates,
    'LANGUAGES': get_languages,
}

def get_setting(name):
    if name in COMPLEX:
        return COMPLEX[name]()
    else:
        return getattr(settings, 'CMS_%s' % name, DEFAULTS[name])
