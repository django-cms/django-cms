from contextlib import contextmanager

from django.conf import settings
from django.urls import LocalePrefixPattern, get_resolver
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from cms.exceptions import LanguageError
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from cms.utils.conf import get_cms_setting, get_site_id


def _ensure_site_id(site_id, name):
    """
    Ensure that the site_id is an integer.
    """
    if site_id is None:
        import warnings

        warnings.warn(
            f"{name} called without specifying 'site_id'. This may lead to unexpected behavior. "
            f"Call {name} with 'site_id=<some_id>' instead.", RemovedInDjangoCMS60Warning, stacklevel=3
        )
        return get_site_id(None)
    return site_id


@contextmanager
def force_language(new_lang):
    old_lang = get_current_language()
    if old_lang != new_lang:
        translation.activate(new_lang)
    yield
    translation.activate(old_lang)


def get_languages(site_id=None):
    site_id = _ensure_site_id(site_id, "get_languages")
    site_id = get_site_id(site_id)
    result = get_cms_setting('LANGUAGES').get(site_id)
    if not result:
        result = []
        defaults = get_cms_setting('LANGUAGES').get('default', {})
        for code, name in settings.LANGUAGES:
            lang = {'code': code, 'name': _(name)}
            lang.update(defaults)
            result.append(lang)
        get_cms_setting('LANGUAGES')[site_id] = result
    return result


def get_site_language_from_request(request, site_id=None):
    from cms.utils import get_current_site

    if site_id is None:
        site_id = get_current_site(request).pk

    # Level 1: language get parameter
    language = request.GET.get('language', None)
    if is_valid_site_language(language, site_id=site_id):
        return language

    # Level 2: LANGUAGE_CODE request parameter
    language = getattr(request, 'LANGUAGE_CODE', None)
    if is_valid_site_language(language, site_id=site_id):
        return language

    # Last resort: default language
    return get_default_language_for_site(site_id=site_id)


def get_language_code(language_code, site_id=None):
    """
    Returns language code while making sure it's in LANGUAGES
    """
    if not language_code:
        return None

    site_id = _ensure_site_id(site_id, "get_language_code")
    languages = get_language_list(site_id)

    if language_code in languages:  # direct hit
        return language_code

    for lang in languages:
        if language_code.split('-')[0] == lang:  # base language hit
            return lang
        if lang.split('-')[0] == language_code:  # base language hit
            return lang
    return language_code


def get_current_language():
    """
    Returns the currently active language

    It's a replacement for Django's translation.get_language() to make sure the
    LANGUAGE_CODE will be found in LANGUAGES.
    Overcomes this issue: https://code.djangoproject.com/ticket/9340
    """
    site_id = getattr(settings, 'SITE_ID', None)
    language_code = translation.get_language()
    if site_id:
        return get_language_code(language_code, site_id=site_id)

    # We do not know the site, return an entry from settings.LANGUAGES
    languages = dict(getattr(settings, 'LANGUAGES', ((language_code, language_code), ))).keys()

    if language_code in languages:
        return language_code  # direct hit

    for lang in languages:
        if language_code.split('-')[0] == lang:  # base language hit
            return lang
        if lang.split('-')[0] == language_code:  # base language hit
            return lang
    return language_code


def get_language_list(site_id=None):
    """
    :return: returns a list of iso2codes for this site
    """
    site_id = _ensure_site_id(site_id, "get_language_list")
    return ([lang['code'] for lang in get_languages(site_id)] if settings.USE_I18N
            else [settings.LANGUAGE_CODE])


def get_language_tuple(site_id=None):
    """
    :return: returns an list of tuples like the old CMS_LANGUAGES or the LANGUAGES for this site
    """
    site_id = _ensure_site_id(site_id, "get_language_tuple")
    return [(lang['code'], lang['name']) for lang in get_languages(site_id)]


def get_language_dict(site_id=None):
    """
    :return: returns an dict of cms languages
    """
    site_id = _ensure_site_id(site_id, "get_language_dict")
    return dict(get_language_tuple(site_id))


def get_public_languages(site_id=None):
    """
    :return: list of iso2codes of public languages for this site
    """
    site_id = _ensure_site_id(site_id, "get_public_languages")
    return [lang['code'] for lang in get_language_objects(site_id)
            if lang.get('public', True)]


def get_language_object(language_code, site_id=None):
    """
    :param language_code: RFC5646 language code
    :return: the language object filled up by defaults
    """
    site_id = _ensure_site_id(site_id, "get_language_object")
    for language in get_languages(site_id):
        if language['code'] == get_language_code(language_code, site_id):
            return language
    raise LanguageError('Language not found: %s' % language_code)


def get_language_objects(site_id=None):
    """
    returns list of all language objects filled up by default values
    """
    site_id = _ensure_site_id(site_id, "get_language_objects")
    return list(get_languages(site_id))


def get_default_language(language_code=None, site_id=None):
    """
    Returns default language depending on settings.LANGUAGE_CODE merged with
    best match from get_cms_setting('LANGUAGES')

    Returns: language_code
    """
    site_id = _ensure_site_id(site_id, "get_default_language")
    if not language_code:
        language_code = get_language_code(settings.LANGUAGE_CODE, site_id=site_id)

    languages = get_language_list(site_id)

    # first try if there is an exact language
    if language_code in languages:
        return language_code

    # otherwise split the language code if possible, so iso3
    language_code = language_code.split("-")[0]

    if language_code not in languages:
        return settings.LANGUAGE_CODE

    return language_code


def get_default_language_for_site(site_id):
    return get_language_list(site_id)[0]


def get_fallback_languages(language, site_id=None):
    """
    returns a list of fallback languages for the given language
    """
    site_id = _ensure_site_id(site_id, "get_fallback_languages")
    try:
        language = get_language_object(language, site_id)
    except LanguageError:
        language = get_languages(site_id)[0]
    return language.get('fallbacks', [])


def get_redirect_on_fallback(language, site_id=None):
    """
    returns if you should redirect on language fallback
    :param language:
    :param site_id:
    :return: Boolean
    """
    site_id = _ensure_site_id(site_id, "get_redirect_on_fallback")
    language = get_language_object(language, site_id)
    return language.get('redirect_on_fallback', True)


def hide_untranslated(language, site_id=None):
    """
    Should untranslated pages in this language be hidden?
    :param language:
    :param site_id:
    :return: A Boolean
    """
    site_id = _ensure_site_id(site_id, "hide_untranslated")
    obj = get_language_object(language, site_id)
    return obj.get('hide_untranslated', True)


def is_language_prefix_patterns_used():
    """
    Returns `True` if the `LocaleRegexURLResolver` or `LocalePrefixPattern`
    is used at root level of the urlpatterns and doesn't have empty
    language_prefix, else it returns `False`.
    """
    for url_pattern in get_resolver(None).url_patterns:
        pattern = getattr(url_pattern, 'pattern', url_pattern)
        if isinstance(pattern, LocalePrefixPattern):
            if pattern.language_prefix != '':
                return True
    return False


def is_valid_site_language(language, site_id):
    return language in get_language_list(site_id)
