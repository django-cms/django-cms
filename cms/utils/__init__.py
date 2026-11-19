# TODO: this is just stuff from utils.py - should be split / moved
import warnings
from typing import TYPE_CHECKING

from django.http import HttpRequest

from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from cms.utils.i18n import (
    get_current_language,
    get_default_language,
    get_language_code,
    get_language_list,
)

if TYPE_CHECKING:
    from django.contrib.sites.models import Site


def get_current_site(request: HttpRequest = None) -> "Site":
    """
    Returns the current Site instance associated with the given request.
    """
    from django.contrib.sites.models import Site

    if request is None:
        warnings.warn(
            "get_current_site() called without request. This may lead to unexpected behavior. "
            "Use get_current_site(request) instead.",
            RemovedInDjangoCMS60Warning,
            stacklevel=2,
        )

    # Allow middleware to identify the site
    request_site = getattr(request, "site", None) if request else None
    if request_site:
        return request_site

    # Fallback to the default site configuration by SITE_ID or through request
    return Site.objects.get_current(request=request)


def get_language_from_request(request: HttpRequest, current_page=None) -> str:
    """
    Return the most obvious language according the request
    """
    if getattr(request, '_cms_language', None):
        return request._cms_language

    site_id = current_page.site_id if current_page else get_current_site(request).pk

    def get_valid_language(language):
        if language:
            language = get_language_code(language, site_id=site_id)
            if language in get_language_list(site_id):
                return language
        return None

    post_language = get_valid_language(request.POST.get('language', None)) if hasattr(request, 'POST') else None
    language = get_valid_language(request.GET.get('language', None)) if hasattr(request, 'GET') else None

    if not language and request:
        # get the active language
        language = get_current_language()
    if language:
        if language not in get_language_list(site_id):
            language = None

    if not language and current_page:
        # in last resort, get the first language available in the page
        languages = current_page.get_languages()

        if len(languages) > 0:
            language = languages[0]

    if not language:
        # language must be defined in CMS_LANGUAGES, so check first if there
        # is any language with LANGUAGE_CODE, otherwise try to split it and find
        # best match
        language = get_default_language(site_id=site_id)

    if post_language and post_language != language:
        # The POST body is the only source for this language: neither the query string,
        # the active language (URL prefix, cookie), nor the page provide it.
        warnings.warn(
            f"The request language '{post_language}' was only determined by the 'language' field of the "
            f"POST body (otherwise '{language}'). Starting with django CMS 6.0, the POST body will not be "
            "considered anymore. Also pass the language in the URL (e.g., the 'language' query parameter "
            "or a language prefix).",
            RemovedInDjangoCMS60Warning,
            stacklevel=2,
        )
        language = post_language

    request._cms_language = language
    return language
