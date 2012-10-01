# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy  as _
from sekizai.helpers import validate_template

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
        for site in settings.CMS_LANGUAGES.keys():
            try:
                int(site)
            except ValueError:
                if not site =="default":
                    raise ImproperlyConfigured("CMS_LANGUAGES can only be filled with integers (site ids) and 'default' for\n"
                                               " default values. %s is not a valid key." % site)
            for lang in settings.CMS_LANGUAGES[site]:
                if site == "default":
                    if lang not in VALID_LANG_PROPS:
                        raise ImproperlyConfigured("CMS_LANGUAGES has an invalid property on the site %(site)s and language %(language)s: %(property)s" % {'site':site, 'language':lang['code'], 'property':key})
                    continue
                if not "code" in lang.keys():
                    raise ImproperlyConfigured("CMS_LANGUAGES has language without a 'code' property")
                if not 'name' in lang.keys():
                    raise ImproperlyConfigured("CMS_LANGUAGES has a language without a 'name' property")
                for key in lang.keys():
                    if key not in VALID_LANG_PROPS:
                        raise ImproperlyConfigured("CMS_LANGUAGES has an invalid property on the site %(site)s and language %(language)s: %(property)s" % {'site':site, 'language':lang['code'], 'property':key})
    except:
        raise ImproperlyConfigured("CMS_LANGUAGES has changed. Please refer to the docs.")







