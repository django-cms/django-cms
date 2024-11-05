import os
from functools import update_wrapper
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from cms import __version__, constants

__all__ = [
    'get_cms_setting',
    'get_site_id'
]


class VERIFIED: pass  # need a unique identifier for CMS_LANGUAGES


def _load_from_file(module_path):
    """
    Load a python module from its absolute filesystem path
    """
    from importlib.machinery import SourceFileLoader

    imported = None
    if module_path:
        imported = SourceFileLoader("mod", module_path).load_module()
    return imported


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
    'DEFAULT_X_FRAME_OPTIONS': constants.X_FRAME_OPTIONS_INHERIT,
    'TOOLBAR_SIMPLE_STRUCTURE_MODE': True,
    'PLACEHOLDER_CONF': {},
    'PLACEHOLDERS': (('', ('content',), _("Single placeholder")),),
    'PERMISSION': False,
    # Whether to use raw ID lookups for users when PERMISSION is True
    'RAW_ID_USERS': False,
    'PUBLIC_FOR': 'all',
    'APPHOOKS': [],
    'TOOLBARS': [],
    'SITE_CHOICES_CACHE_KEY': 'CMS:site_choices',
    'PAGE_CHOICES_CACHE_KEY': 'CMS:page_choices',
    'MEDIA_PATH': 'cms/',
    'PAGE_MEDIA_PATH': 'cms_page_media/',
    'TITLE_CHARACTER': '+',
    'PAGE_CACHE': True,
    'PLACEHOLDER_CACHE': True,
    'PLUGIN_CACHE': True,
    'CACHE_PREFIX': f'cms_{__version__}_',
    'PLUGIN_PROCESSORS': [],
    'PLUGIN_CONTEXT_PROCESSORS': [],
    'UNIHANDECODE_VERSION': None,
    'UNIHANDECODE_DECODERS': ['ja', 'zh', 'kr', 'vn', 'diacritic'],
    'UNIHANDECODE_DEFAULT_DECODER': 'diacritic',
    'TOOLBAR_ANONYMOUS_ON': True,
    'TOOLBAR_URL__PERSIST': 'persist',
    'TOOLBAR_URL__DISABLE': 'toolbar_off',
    'TOOLBAR_URL__ENABLE': 'toolbar_on',
    'ADMIN_NAMESPACE': 'admin',
    'APP_NAME': None,
    'TOOLBAR_HIDE': False,
    'INTERNAL_IPS': [],
    'REQUEST_IP_RESOLVER': 'cms.utils.request_ip_resolvers.default_request_ip_resolver',
    'PAGE_WIZARD_DEFAULT_TEMPLATE': constants.TEMPLATE_INHERITANCE_MAGIC,
    'PAGE_WIZARD_CONTENT_PLUGIN': 'TextPlugin',
    'PAGE_WIZARD_CONTENT_PLUGIN_BODY': 'body',
    'PAGE_WIZARD_CONTENT_PLACEHOLDER': None,  # Use first placeholder it finds.
    'SIDEFRAME_ENABLED': True,
    'CONFIRM_VERSION4': False,
    'ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED': False,
    'ENDPOINT_LIVE_URL_QUERYSTRING_PARAM': "live-url",
    'REDIRECT_PRESERVE_QUERY_PARAMS': False,
    'REDIRECT_TO_LOWERCASE_SLUG': False,
    'HIDE_LEGACY_FEATURES': True,
    'COLOR_SCHEME': 'auto',
    'COLOR_SCHEME_TOGGLE': True,
}


def get_cache_durations():
    """
    Returns the setting: CMS_CACHE_DURATIONS or the defaults.
    """
    return getattr(settings, 'CMS_CACHE_DURATIONS', {
        'menus': 60 * 60,
        'content': 60,
        'permissions': 60 * 60,
    })


@default('CMS_MEDIA_ROOT')
def get_media_root():
    return os.path.join(settings.MEDIA_ROOT, get_cms_setting('MEDIA_PATH'))


@default('CMS_MEDIA_URL')
def get_media_url():
    return urljoin(settings.MEDIA_URL, get_cms_setting('MEDIA_PATH'))


@default('CMS_TOOLBAR_URL__PERSIST')
def get_toolbar_url__persist():
    return get_cms_setting('TOOLBAR_URL__PERSIST')


@default('CMS_TOOLBAR_URL__DISABLE')
def get_toolbar_url__disable():
    return get_cms_setting('TOOLBAR_URL__DISABLE')


@default('CMS_TOOLBAR_URL__ENABLE')
def get_toolbar_url__enable():
    return get_cms_setting('TOOLBAR_URL__ENABLE')


def get_templates():
    if getattr(settings, 'CMS_TEMPLATES_DIR', False):
        tpldir = getattr(settings, 'CMS_TEMPLATES_DIR', False)
        # CMS_TEMPLATES_DIR can either be a string pointing to the templates directory
        # or a dictionary holding 'site: template dir' entries
        if isinstance(tpldir, dict):
            tpldir = tpldir[settings.SITE_ID]
        # We must extract the relative path of CMS_TEMPLATES_DIR to the nearest
        # valid templates' directory. Here we mimic what the filesystem and
        # app_directories template loaders do
        prefix = ''
        # Relative to TEMPLATE['DIRS'] for filesystem loader

        path = [template['DIRS'][0] for template in settings.TEMPLATES]

        for basedir in path:
            if tpldir.find(basedir) == 0:
                prefix = tpldir.replace(basedir + os.sep, '')
                break
        # Relative to 'templates' directory that app_directory scans
        if not prefix:
            components = tpldir.split(os.sep)
            try:
                prefix = os.path.join(*components[components.index('templates') + 1:])
            except ValueError:
                # If templates is not found we use the directory name as prefix
                # and hope for the best
                prefix = os.path.basename(tpldir)
        config_path = os.path.join(tpldir, '__init__.py')
        # Try to load templates list and names from the template module
        # If module file is not present skip configuration and just dump the filenames as templates
        if os.path.isfile(config_path):
            template_module = _load_from_file(config_path)
            templates = [
                (os.path.join(prefix, data[0].strip()), data[1]) for data in template_module.TEMPLATES.items()
            ]
        else:
            templates = list((os.path.join(prefix, tpl), tpl) for tpl in os.listdir(tpldir))
    else:
        templates = list(getattr(settings, 'CMS_TEMPLATES', []))
    if get_cms_setting('TEMPLATE_INHERITANCE') and templates:
        templates.append((constants.TEMPLATE_INHERITANCE_MAGIC, _('Inherit the template of the nearest ancestor')))
    return templates


def get_placeholders():
    if getattr(settings, 'CMS_PLACEHOLDERS', False):
        return settings.CMS_PLACEHOLDERS
    if getattr(settings, 'CMS_TEMPLATES', False) or getattr(settings, 'CMS_TEMPLATES_DIR', False):
        return ()
    return DEFAULTS['PLACEHOLDERS']


def _ensure_languages_settings(languages):
    valid_language_keys = ['code', 'name', 'fallbacks', 'hide_untranslated', 'redirect_on_fallback', 'public']
    required_language_keys = ['code', 'name']
    simple_defaults = ['public', 'redirect_on_fallback', 'hide_untranslated']

    if not isinstance(languages, dict):
        raise ImproperlyConfigured(
            "CMS_LANGUAGES must be a dictionary with site IDs and 'default'"
            " as keys. Please check the format.")

    defaults = languages.pop('default', {})
    default_fallbacks = defaults.get('fallbacks')
    needs_fallbacks = []

    for key in defaults:
        if key not in valid_language_keys:
            raise ImproperlyConfigured("CMS_LANGUAGES has an invalid property in the default properties: %s" % key)

    for key in simple_defaults:
        if key not in defaults:
            defaults[key] = True

    for site, language_list in languages.items():
        if site != hash(site):
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
                        f"CMS_LANGUAGES has invalid key {key!r} in language {language_code!r} in site {site!r}"
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
        language_object['fallbacks'] = [
            lang_code for lang_code in site_fallbacks[site] if lang_code != language_object['code']
        ]

    languages['default'] = defaults
    languages[VERIFIED] = True  # this will be busted by @override_settings and cause a re-check

    return languages


def get_languages():
    if settings.SITE_ID != hash(settings.SITE_ID):
        raise ImproperlyConfigured(
            "SITE_ID must be an integer"
        )
    if not settings.USE_I18N:
        return _ensure_languages_settings(
            {settings.SITE_ID: [{'code': settings.LANGUAGE_CODE, 'name': settings.LANGUAGE_CODE}]})
    if settings.LANGUAGE_CODE not in dict(settings.LANGUAGES):
        raise ImproperlyConfigured(
            'LANGUAGE_CODE "%s" must have a matching entry in LANGUAGES' % settings.LANGUAGE_CODE
        )
    languages = getattr(settings, 'CMS_LANGUAGES', {
        settings.SITE_ID: [{'code': code, 'name': _(name)} for code, name in settings.LANGUAGES]
    })
    if VERIFIED in languages:
        return languages
    return _ensure_languages_settings(languages)


def get_unihandecode_host():
    host = getattr(settings, 'CMS_UNIHANDECODE_HOST', None)
    if not host:
        return host
    if host.endswith('/'):
        return host
    else:
        return host + '/'


COMPLEX = {
    'CACHE_DURATIONS': get_cache_durations,
    'MEDIA_ROOT': get_media_root,
    'MEDIA_URL': get_media_url,
    # complex because not prefixed by CMS_
    'TEMPLATES': get_templates,
    'PLACEHOLDERS': get_placeholders,
    'LANGUAGES': get_languages,
    'UNIHANDECODE_HOST': get_unihandecode_host,
    'CMS_TOOLBAR_URL__PERSIST': get_toolbar_url__persist,
    'CMS_TOOLBAR_URL__DISABLE': get_toolbar_url__disable,
    'CMS_TOOLBAR_URL__ENABLE': get_toolbar_url__enable,
}


def get_cms_setting(name):
    if name in COMPLEX:
        return COMPLEX[name]()
    return getattr(settings, 'CMS_%s' % name, DEFAULTS[name])


def get_site_id(site):
    from django.contrib.sites.models import Site
    if isinstance(site, Site):
        return site.id
    try:
        return int(site)
    except (TypeError, ValueError):
        pass
    return settings.SITE_ID
