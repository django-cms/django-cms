import logging
import re
from contextlib import contextmanager

from django.conf import settings
from django.urls import LocalePrefixPattern, get_resolver
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from cms.exceptions import LanguageError
from cms.utils.conf import get_cms_setting, get_site_id

logger = logging.getLogger(__name__)


@contextmanager
def force_language(new_lang):
    old_lang = get_current_language()
    if old_lang != new_lang:
        translation.activate(new_lang)
    yield
    translation.activate(old_lang)


def get_languages(site_id):
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


#: What a language tag may be made of (RFC 5646 is subtags of letters and
#: digits joined by hyphens). Used to tell "a language this site does not
#: serve" -- which a caller may legitimately pass -- from "not a language at
#: all", which no caller means and which must not be handed on.
_LANGUAGE_TAG = re.compile(r'^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$')

#: The widest language code cms can store. Every ``language`` column in cms is
#: ``max_length=15`` -- ``CMSPlugin``, ``PageContent``, ``Page.urls`` -- so a
#: longer value cannot be a language this installation can use, whatever its
#: shape, and is refused here rather than at the INSERT.
#: ``cms.tests.test_i18n`` asserts this matches the narrowest of those columns,
#: so widening a field cannot silently leave this behind.
MAX_LANGUAGE_CODE_LENGTH = 15


def get_language_code(language_code, site_id):
    """
    Returns language code while making sure it's in LANGUAGES
    """
    if not language_code:
        return None

    if (not _LANGUAGE_TAG.match(language_code)
            or len(language_code) > MAX_LANGUAGE_CODE_LENGTH):
        # Not a language tag by any reading, so there is nothing to match and
        # nothing to hand back. Returning it unchanged -- which is what the
        # fall-through below used to do -- let a value that merely arrived in a
        # ?language query travel on as this site's language.
        #
        # That is how a malformed cms_path took down plugin saving: the editor
        # URL carried `?language=en-gb?language=en-gb`, parse_qsl read the
        # language as `en-gb?language=en-gb`, nothing here matched it on a site
        # serving only `en-gb`, and the 20-character "language" went into the
        # operation context -- and from there into djangocms-history's
        # `language` column, which is a varchar(15) like cms's own. Postgres
        # refused it and every Text plugin save answered 500.
        #
        # Length is checked alongside shape because a *syntactically* valid
        # tag can still overflow: `"a" * 40` matches the pattern above and was
        # handed straight back, so the original varchar(15) failure stayed
        # reachable through a different input. Measured on the live database
        # after the shape fix was in place -- the shape check alone was not the
        # whole invariant.
        #
        # The site's default is returned instead, and the value is named in
        # the log, because a non-language here means something upstream built a
        # bad URL and that should be visible rather than absorbed.
        logger.warning(
            "Ignoring %r, which is not a usable language code (it is not a "
            "language tag, or is longer than the %d characters a language "
            "code may be), and using this site's default instead. "
            "Something built a malformed language value -- a doubled query "
            "string in a URL will do it.",
            language_code, MAX_LANGUAGE_CODE_LENGTH,
        )
        return get_default_language(site_id=site_id)

    languages = get_language_list(site_id)

    if language_code in languages:  # direct hit
        return language_code

    for lang in languages:
        if language_code.split('-')[0] == lang:  # base language hit
            return lang
        if lang.split('-')[0] == language_code:  # base language hit
            return lang
    # A language tag this site does not serve is handed back as it arrived: it
    # may be served by another site in the same project, and deciding for the
    # caller here would hide a real misconfiguration.
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


def get_language_list(site_id):
    """
    :return: returns a list of iso2codes for this site
    """
    return ([lang['code'] for lang in get_languages(site_id)] if settings.USE_I18N
            else [settings.LANGUAGE_CODE])


def get_language_tuple(site_id):
    """
    :return: returns an list of tuples like the old CMS_LANGUAGES or the LANGUAGES for this site
    """
    return [(lang['code'], lang['name']) for lang in get_languages(site_id)]


def get_language_dict(site_id):
    """
    :return: returns an dict of cms languages
    """
    return dict(get_language_tuple(site_id))


def get_public_languages(site_id):
    """
    :return: list of iso2codes of public languages for this site
    """
    return [lang['code'] for lang in get_language_objects(site_id)
            if lang.get('public', True)]


def get_language_object(language_code, site_id):
    """
    :param language_code: RFC5646 language code
    :return: the language object filled up by defaults
    """
    for language in get_languages(site_id):
        if language['code'] == get_language_code(language_code, site_id):
            return language
    raise LanguageError('Language not found: %s' % language_code)


def get_language_objects(site_id):
    """
    returns list of all language objects filled up by default values
    """
    return list(get_languages(site_id))


def get_default_language(language_code=None, site_id=None):
    """
    Returns default language depending on settings.LANGUAGE_CODE merged with
    best match from get_cms_setting('LANGUAGES')

    Returns: language_code
    """
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


def get_fallback_languages(language, site_id):
    """
    returns a list of fallback languages for the given language
    """
    try:
        language = get_language_object(language, site_id)
    except LanguageError:
        language = get_languages(site_id)[0]
    return language.get('fallbacks', [])


def get_redirect_on_fallback(language, site_id):
    """
    returns if you should redirect on language fallback
    :param language:
    :param site_id:
    :return: Boolean
    """
    language = get_language_object(language, site_id)
    return language.get('redirect_on_fallback', True)


def hide_untranslated(language, site_id):
    """
    Should untranslated pages in this language be hidden?
    :param language:
    :param site_id:
    :return: A Boolean
    """
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
