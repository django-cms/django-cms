# -*- coding: utf-8 -*-
from cms.exceptions import CMSDeprecationWarning
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy  as _
from sekizai.helpers import validate_template
import warnings

def pre_patch():
    """Patch settings for dynamic defaults"""
    if not getattr(settings, 'CMS_LANGUAGES', False):
        settings.CMS_LANGUAGES = {settings.SITE_ID:[]}
        for code, name in settings.LANGUAGES:
            lang = {'code':code, 'name':_(name)}
            settings.CMS_LANGUAGES[settings.SITE_ID].append(lang)

def post_patch():
    """Patch settings after global are added
    """
    if settings.CMS_TEMPLATE_INHERITANCE:
        # Append the magic inheritance template
        settings.CMS_TEMPLATES = tuple(settings.CMS_TEMPLATES) + (
            (settings.CMS_TEMPLATE_INHERITANCE_MAGIC, _('Inherit the template of the nearest ancestor')),
        ) 


def post_patch_check():
    """Post patch check, just make sure there isn't any misconfiguration. All
    the code for checking settings should go here.
    """

    # Ensure templates are set, and more than just the inheritance setting.
    cms_templates_length = len(settings.CMS_TEMPLATES)
    if (cms_templates_length < 1 or
        (cms_templates_length == 1 and settings.CMS_TEMPLATES[0][0] == settings.CMS_TEMPLATE_INHERITANCE_MAGIC)):
        raise ImproperlyConfigured('Please make sure you specified a CMS_TEMPLATES setting.')
    
    # check if is user middleware installed
    if settings.CMS_PERMISSION and not 'cms.middleware.user.CurrentUserMiddleware' in settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('CMS Permission system requires cms.middleware.user.CurrentUserMiddleware.\n'
            'Please put it into your MIDDLEWARE_CLASSES in settings file')
    
    # check sekizai namespaces
    try:
        from django.template.loaders.app_directories import Loader
    except ImportError:
        return # south...
    for template in settings.CMS_TEMPLATES:
        if template[0] == settings.CMS_TEMPLATE_INHERITANCE_MAGIC:
            continue
        if not validate_template(template[0], ['js', 'css']):
            raise ImproperlyConfigured(
                "The 'js' and 'css' sekizai namespaces must be present in each template, "
                "- or a template it inherits from - defined in CMS_TEMPLATES. "
                "I can't find the namespaces in %r."
                % template[0]
            )
    VALID_LANG_PROPS = ['code', 'name', 'fallbacks', 'hide_untranslated', 'redirect_on_fallback', 'public']
    try:
        for site in settings.CMS_LANGUAGES:
            try:
                int(site)
            except ValueError:
                if not site =="default":
                    raise ImproperlyConfigured("CMS_LANGUAGES can only be filled with integers (site ids) and 'default'"
                                               " for default values. %s is not a valid key." % site)
            for language in settings.CMS_LANGUAGES[site]:
                if site == "default":
                    if language not in VALID_LANG_PROPS:
                        raise ImproperlyConfigured("CMS_LANGUAGES has an invalid property in the default properties: %(property)s" %
                                                   {'property':language})
                    continue
                if not "code" in language.keys():
                    raise ImproperlyConfigured("CMS_LANGUAGES has a language without a 'code' property")
                if not 'name' in language.keys():
                    raise ImproperlyConfigured("CMS_LANGUAGES has a language without a 'name' property")
                for key in language:
                    if key not in VALID_LANG_PROPS:
                        raise ImproperlyConfigured("CMS_LANGUAGES has an invalid property on the site %(site)s and "
                                                   "language %(language)s: %(property)s" %
                                                   {'site':site, 'language':language['code'], 'property':key})
                # Fill up the defaults
                if not language.has_key('fallbacks'):
                    fallbacks = []
                    for tmp_language in settings.CMS_LANGUAGES[site]:
                        tmp_language = tmp_language.copy()
                        if not tmp_language.has_key('public'):
                            if settings.CMS_LANGUAGES.has_key('default'):
                                tmp_language['public'] = settings.CMS_LANGUAGES['default'].get('public', True)
                            else:
                                tmp_language['public'] = True
                        if tmp_language['public']:
                            fallbacks.append(tmp_language['code'])
                    if fallbacks:
                        fallbacks.remove(language['code'])
                    if settings.CMS_LANGUAGES.has_key('default'):
                        language['fallbacks'] = settings.CMS_LANGUAGES['default'].get('fallbacks', fallbacks)
                    else:
                        language['fallbacks'] = fallbacks
                if not language.has_key('public'):
                    if settings.CMS_LANGUAGES.has_key('default'):
                        language['public'] = settings.CMS_LANGUAGES['default'].get('public', True)
                    else:
                        language['public'] = True
                if not language.has_key('redirect_on_fallback'):
                    if settings.CMS_LANGUAGES.has_key('default'):
                        language['redirect_on_fallback'] = settings.CMS_LANGUAGES['default'].get('redirect_on_fallback', True)
                    else:
                        language['redirect_on_fallback'] = True
                if not language.has_key('hide_untranslated'):
                    if settings.CMS_LANGUAGES.has_key('default'):
                        language['hide_untranslated'] = settings.CMS_LANGUAGES['default'].get('hide_untranslated', True)
                    else:
                        language['hide_untranslated'] = True
    except TypeError:
        if type(settings.CMS_LANGUAGES) == tuple:
            new_languages = {}
            lang_template = {'code':'', 'name':'', 'fallbacks':[],'public':True, 'redirect_on_fallback':True, 'hide_untranslated':False}
            if hasattr(settings,'CMS_HIDE_UNTRANSLATED'):
                lang_template['hide_untranslated'] = settings.CMS_HIDE_UNTRANSLATED
            if hasattr(settings, 'CMS_SITE_LANGUAGES'):
                for site in settings.CMS_SITE_LANGUAGES:
                    new_languages[site] = []
            else:
                new_languages[1]=[]

            if hasattr(settings, 'CMS_SITE_LANGUAGES'):
                for site in settings.CMS_SITE_LANGUAGES:
                    for site_code in settings.CMS_SITE_LANGUAGES[site]:
                        for code, name in settings.CMS_LANGUAGES:
                            if code == site_code:
                                new_languages[site].append(get_old_language_conf(code, name, lang_template))
            else:
                for code, name in settings.CMS_LANGUAGES:
                    new_languages[1].append(get_old_language_conf(code, name, lang_template))
            settings.CMS_LANGUAGES = new_languages
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            warnings.warn(
                "CMS_LANGUAGES has changed in django-cms 2.4\nYou may replace CMS_LANGUAGES with the following:\n%s" % pp.pformat(settings.CMS_LANGUAGES),
                CMSDeprecationWarning)

        else:
            raise ImproperlyConfigured("CMS_LANGUAGES has changed and has some errors. Please refer to the docs.")


def get_old_language_conf(code, name, template):
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


