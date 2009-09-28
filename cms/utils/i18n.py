from django.conf import settings
from cms import settings as cms_settings
from django.core.exceptions import ImproperlyConfigured

def get_default_language():
    """Returns default language depending on settings.LANGUAGE_CODE merged with
    best match from settings.CMS_LANGUAGES
    
    Returns: language_code
    
    Raises ImproperlyConfigured if no match found
    """
    
    language_codes = dict(cms_settings.CMS_LANGUAGES).keys()
    
    # first try if there is an exact language
    if settings.LANGUAGE_CODE in language_codes:
        return settings.LANGUAGE_CODE 
    
    # otherwise split the language code if possible, so iso3
    language_code = settings.LANGUAGE_CODE.split("-")[0]
    
    if not language_code in language_codes:
        raise ImproperlyConfigured("No match in CMS_LANGUAGES for LANGUAGE_CODE %s" % settings.LANGUAGE_CODE)
    
    return language_code