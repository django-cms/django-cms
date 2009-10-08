from django.conf import settings
from cms import settings as cms_settings
from django.core.exceptions import ImproperlyConfigured

def get_default_language(language_code=None):
    """Returns default language depending on settings.LANGUAGE_CODE merged with
    best match from settings.CMS_LANGUAGES
    
    Returns: language_code
    
    Raises ImproperlyConfigured if no match found
    """
    
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    
    languages = dict(cms_settings.CMS_LANGUAGES).keys()
    
    # first try if there is an exact language
    if language_code in languages:
        return language_code
    
    # otherwise split the language code if possible, so iso3
    language_code = language_code.split("-")[0]
    
    if not language_code in languages:
        raise ImproperlyConfigured("No match in CMS_LANGUAGES for LANGUAGE_CODE %s" % settings.LANGUAGE_CODE)
    
    return language_code

def get_fallback_languages(language):
    """
    returns a list of fallback languages for the given language
    """
    conf = cms_settings.CMS_LANGUAGE_CONF
    if language in conf:
        l_list = conf[language]
    else:
        languages = cms_settings.CMS_LANGUAGES
        l_list = []
        for l in languages:
            l_list.append(l[0])
    if language in l_list:
        l_list.remove(language)
    return l_list
    
    
    
    
