# -*- coding: utf-8 -*-
# TODO: this is just stuff from utils.py - should be splitted / moved
from functools import lru_cache

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject
from django.urls import resolve
from django.contrib.contenttypes.models import ContentType
from django.urls.exceptions import Resolver404

from cms.utils.conf import get_site_id  # nopyflakes
from cms.utils.i18n import get_default_language
from cms.utils.i18n import get_language_list
from cms.utils.i18n import get_language_code


def get_current_site():
    from django.contrib.sites.models import Site

    return Site.objects.get_current()


@lru_cache(512)
def get_object_language(request):
    """
    We resolve the request and try to get content type if there is one.
    If the content type has a language, it's the language we want to use.
    """
    try:
        resolved = resolve(request.path)
    except Resolver404:
        return None

    args = resolved.args
    if len(args) != 2 or not all([a.isnumeric() for a in args]):
        # if it is not a content type we can't get a language from it.
        return None

    content_type_id, object_id = args

    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
        content_type_obj = content_type.get_object_for_this_type(pk=object_id)
        language = content_type_obj.language
    except (ContentType.DoesNotExist, AttributeError):
        return None

    return language


def get_language_from_request(request, current_page=None):
    """
    Return the most obvious language according the request
    """
    language = None
    if hasattr(request, 'POST'):
        language = request.POST.get('language', None)
    elif hasattr(request, 'GET'):
        language = request.GET.get('language', None)

    if not language:
        # if we still don't have language from get or post request
        # we try to get it from the content object of the request.
        language = get_object_language(request)

    site_id = current_page.node.site_id if current_page else None
    if language:
        language = get_language_code(language)
        if not language in get_language_list(site_id):
            language = None
    if not language:
        language = get_language_code(getattr(request, 'LANGUAGE_CODE', None))
    if language:
        if not language in get_language_list(site_id):
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

default_storage = 'django.contrib.staticfiles.storage.StaticFilesStorage'


class ConfiguredStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(getattr(settings, 'STATICFILES_STORAGE', default_storage))()

configured_storage = ConfiguredStorage()
