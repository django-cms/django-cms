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