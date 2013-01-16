# -*- coding: utf-8 -*-
from functools import update_wrapper
import pprint
import urlparse
from cms import constants
from cms.exceptions import CMSDeprecationWarning
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
import os
import warnings


__all__ = ['get_cms_setting']


class VERIFIED: pass # need a unique identifier for CMS_LANGUAGES


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
        'content': get_cms_setting('CONTENT_CACHE_DURATION'),
        'permissions': 60 * 60,
    }

@default('CMS_MEDIA_ROOT')
def get_media_root():
    return os.path.join(settings.MEDIA_ROOT, get_cms_setting('MEDIA_PATH'))

@default('CMS_MEDIA_ROOT')
def get_media_url():
    return urlparse.urljoin(settings.MEDIA_URL, get_cms_setting('MEDIA_PATH'))

@default('PLACEHOLDER_FRONTEND_EDITING')
def get_placeholder_frontend_editing():
    return True

def get_templates():
    templates = list(getattr(settings, 'CMS_TEMPLATES', []))
    if get_cms_setting('TEMPLATE_INHERITANCE'):
        templates.append((constants.TEMPLATE_INHERITANCE_MAGIC, _('Inherit the template of the nearest ancestor')))
    return templates


def _ensure_languages_settings_new(languages):
    valid_language_keys = ['code', 'name', 'fallbacks', 'hide_untranslated', 'redirect_on_fallback', 'public']
    required_language_keys = ['code', 'name']
    simple_defaults = ['public', 'redirect_on_fallback', 'hide_untranslated']

    defaults = languages.pop('default', {})
    default_fallbacks = defaults.get('fallbacks')
    needs_fallbacks = []

    for key in defaults:
        if key not in valid_language_keys:
            raise ImproperlyConfigured("CMS_LANGUAGES has an invalid property in the default properties: s" % key)

    for key in simple_defaults:
        if key not in defaults:
            defaults[key] = True

    for site, language_list in languages.items():
        if not isinstance(site, int):
            raise ImproperlyConfigured(
                "CMS_LANGUAGES can only be filled with integers (site IDs) and 'default'"
                " for default values. %s is not a valid key." % site)

        for language_object in language_list:
            for required_key in required_language_keys:
                if required_key not in language_object:
                    raise ImproperlyConfigured("CMS_LANGUAGES has a language which is missing the required key %r "
                        "in site %r" % (key, site))
            language_code = language_object['code']
            for key in language_object:
                if key not in valid_language_keys:
                    raise ImproperlyConfigured(
                        "CMS_LANGUAGES has invalid key %r in language %r in site %r" % (key, language_code, site)
                    )

            if 'fallbacks' not in language_object:
                if default_fallbacks:
                    language_object['fallbacks'] = default_fallbacks
                else:
                    needs_fallbacks.append((site, language_object))
            for key in simple_defaults:
                if key not in language_object:
                    language_object[key] = defaults[key]

    site_fallbacks = {}
    for site, language_object in needs_fallbacks:
        if site not in site_fallbacks:
            site_fallbacks[site] = [lang['code'] for lang in languages[site] if lang['public']]
        language_object['fallbacks'] = [lang_code for lang_code in site_fallbacks[site] if lang_code != language_object['code']]

    languages['default'] = defaults

    return languages

def _get_old_language_conf(code, name, template):
    language = template.copy()
    language['code'] = code
    language['name'] = name
    default_fallbacks = dict(settings.CMS_LANGUAGES).keys()
    if hasattr(settings, 'CMS_LANGUAGE_FALLBACK'):
        if settings.CMS_LANGUAGE_FALLBACK:
            if hasattr(settings, 'CMS_LANGUAGE_CONF'):
                language['fallbacks'] = settings.CMS_LANGUAGE_CONF.get(code, default_fallbacks)
            else:
                language['fallbacks'] = default_fallbacks
        else:
            language['fallbacks'] = []
    else:
        if hasattr(settings, 'CMS_LANGUAGE_CONF'):
            language['fallbacks'] = settings.CMS_LANGUAGE_CONF.get(code, default_fallbacks)
        else:
            language['fallbacks'] = default_fallbacks
    if hasattr(settings, 'CMS_FRONTEND_LANGUAGES'):
        language['public'] = code in settings.CMS_FRONTEND_LANGUAGES
    return language

def _translate_legacy_languages_settings(languages):
    new_languages = {}
    lang_template = {'fallbacks': [], 'public': True, 'redirect_on_fallback': True,
                     'hide_untranslated': getattr(settings, 'CMS_HIDE_UNTRANSLATED', False)}
    codes = dict(languages)
    for site, site_languages in getattr(settings, 'CMS_SITE_LANGUAGES', {1: languages}).items():
        new_languages[site] = []
        for site_language in site_languages:
            if site_language in codes:
                new_languages[site].append(_get_old_language_conf(site_language, codes[site_language], lang_template))

    pp = pprint.PrettyPrinter(indent=4)
    warnings.warn("CMS_LANGUAGES has changed in django-cms 2.4\n"
        "You may replace CMS_LANGUAGES with the following:\n%s" % pp.pformat(new_languages),
        CMSDeprecationWarning)
    new_languages['default'] = lang_template.copy()
    return new_languages

def _ensure_languages_settings(languages):
    if isinstance(languages, dict):
        verified_languages = _ensure_languages_settings_new(languages)
    else:
        verified_languages = _translate_legacy_languages_settings(languages)
    verified_languages[VERIFIED] = True # this will be busted by SettingsOverride and cause a re-check
    return verified_languages

def get_languages():
    languages = getattr(settings, 'CMS_LANGUAGES', {
        settings.SITE_ID: [{'code': code, 'name': _(name)} for code, name in settings.LANGUAGES]
    })
    if VERIFIED in languages:
        return languages
    return _ensure_languages_settings(languages)

COMPLEX = {
    'CACHE_DURATIONS': get_cache_durations,
    'MEDIA_ROOT': get_media_root,
    'MEDIA_URL': get_media_url,
    # complex because not prefixed by CMS_
    'PLACEHOLDER_FRONTEND_EDITING': get_placeholder_frontend_editing,
    'TEMPLATES': get_templates,
    'LANGUAGES': get_languages,
}

def get_cms_setting(name):
    if name in COMPLEX:
        return COMPLEX[name]()
    else:
        return getattr(settings, 'CMS_%s' % name, DEFAULTS[name])
