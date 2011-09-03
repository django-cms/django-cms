# -*- coding: utf-8 -*-
from django.conf import settings

def get_default_language(language_code=None):
    """Returns default language depending on settings.LANGUAGE_CODE merged with
    best match from settings.CMS_LANGUAGES
    
    Returns: language_code
    """
    
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    
    languages = dict(settings.CMS_LANGUAGES).keys()
    
    # first try if there is an exact language
    if language_code in languages:
        return language_code
    
    # otherwise split the language code if possible, so iso3
    language_code = language_code.split("-")[0]
    
    if not language_code in languages:
        return settings.LANGUAGE_CODE
    
    return language_code

def get_fallback_languages(language):
    """
    returns a list of fallback languages for the given language
    """
    conf = settings.CMS_LANGUAGE_CONF
    if language in conf:
        l_list = conf[language]
    else:
        languages = settings.CMS_LANGUAGES
        l_list = []
        for lang in languages:
            l_list.append(lang[0])
    if language in l_list:
        l_list.remove(language)
    return l_list
    
    
    
    
