# TODO: this is just stuff from utils.py - should be split / moved

from cms.utils.i18n import (
    get_current_language,
    get_default_language,
    get_language_code,
    get_language_list,
)


def get_current_site():
    from django.contrib.sites.models import Site

    return Site.objects.get_current()


def get_language_from_request(request, current_page=None):
    """
    Return the most obvious language according the request
    """
    language = None
    if hasattr(request, 'POST'):
        language = request.POST.get('language', None)
    if hasattr(request, 'GET') and not language:
        language = request.GET.get('language', None)
    site_id = current_page.node.site_id if current_page else None
    if language:
        language = get_language_code(language)
        if language not in get_language_list(site_id):
            language = None
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

    return language
