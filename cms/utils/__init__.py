# TODO: this is just stuff from utils.py - should be split / moved
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
        import warnings

        warnings.warn(
            "get_current_site() called without request. This may lead to unexpected behavior. "
            "Use get_current_site(request) instead.",
            RemovedInDjangoCMS60Warning,
            stacklevel=2,
        )

    return Site.objects.get_current(request=request)


def get_language_from_request(request: HttpRequest, current_page=None) -> str:
    """
    Return the most obvious language according the request
    """
    if getattr(request, '_cms_language', None):
        return request._cms_language

    language = None
    if hasattr(request, 'POST'):
        language = request.POST.get('language', None)
    if hasattr(request, 'GET') and not language:
        language = request.GET.get('language', None)
    site_id = current_page.site_id if current_page else get_current_site(request).pk
    if language:
        language = get_language_code(language, site_id=site_id)
        if language not in get_language_list(site_id):
            language = None
    if not language and request:
        # get the active language
        language = get_current_language()
        request._cms_language = language
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

    return language
