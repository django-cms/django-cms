"""The frontend-editing URL contract.

Answers "what is the edit / preview / structure / live URL for this object?" and
"which sibling object represents language X?". Every container needs these --
menus, pages, core and the toolbar all build editing links -- so they live in
``shared`` rather than behind any one container.

Moved here from ``cms.toolbar.utils``. None of it is about the toolbar; that
import is the reason ``menus`` appeared to depend on the toolbar container.
"""

from __future__ import annotations

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import QueryDict
from django.urls import NoReverseMatch
from django.utils.translation import (
    get_language,
    get_language_from_path,
    override as force_language,
)

from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse

__all__ = [
    "add_live_url_querystring_param",
    "get_object_edit_url",
    "get_object_for_language",
    "get_object_live_url",
    "get_object_preview_url",
    "get_object_structure_url",
]


def add_live_url_querystring_param(obj: models.Model, url: str, language: str | None = None) -> str:
    """
    Append a live url to a given object url using a supplied url parameter configured
    by the setting: CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM

    :param obj: Placeholder source object
    :param url: Url string
    :param language: The current language code or None
    :returns: A url string
    """
    url_param = get_cms_setting('ENDPOINT_LIVE_URL_QUERYSTRING_PARAM')
    if not hasattr(obj, "get_absolute_url"):
        return url
    try:
        live_url = obj.get_absolute_url()
    except NoReverseMatch:
        return url
    url_fragments = url.split('?')
    if len(url_fragments) > 1:
        url += f'&{url_param}={live_url}'
    else:
        url += f'?{url_param}={live_url}'
    return url


def _get_object_url(reverse_name: str, obj: models.Model, language: str = None, params: QueryDict | None = None) -> str:
    content_type = ContentType.objects.get_for_model(obj)

    language = getattr(obj, "language", language)  # Object trumps parameter
    if language is None:
        language = get_language()

    with force_language(language):
        url = admin_reverse(reverse_name, args=[content_type.pk, obj.pk])
        get_params = params.copy() if params else QueryDict(mutable=True)
        if not get_language_from_path(url):
            get_params["language"] = language
        if get_params:
            url = url + "?" + get_params.urlencode()
    if get_cms_setting("ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED"):
        url = add_live_url_querystring_param(obj, url, language)
    return url


def get_object_edit_url(obj: models.Model, language: str | None = None, params: QueryDict | None = None) -> str:
    """
    Returns the url of the edit endpoint for the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.

    params is an optional QueryDict to be added to the URL.
    """
    return _get_object_url("cms_placeholder_render_object_edit", obj, language, params)


def get_object_preview_url(obj: models.Model, language: str | None = None, params: QueryDict | None = None) -> str:
    """
    Returns the url of the preview endpoint for the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.

    params is an optional QueryDict to be added to the URL.
    """
    return _get_object_url("cms_placeholder_render_object_preview", obj, language, params)


def get_object_structure_url(obj: models.Model, language: str | None = None, params: QueryDict | None = None) -> str:
    """
    Returns the url of the structure endpoint for the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.

    params is an optional QueryDict to be added to the URL.

    """
    return _get_object_url("cms_placeholder_render_object_structure", obj, language, params)


def get_object_live_url(obj: models.Model, language: str | None = None, site: Site | None = None, params: QueryDict | None = None) -> str | None:
    """
    Returns the live url of the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.
    If the object - or its grouper - has no site property, the site argument is ignored.
    """
    if not hasattr(obj, "get_absolute_url"):
        return None

    language = getattr(obj, "language", language)  # Object trumps parameter
    if language is None:
        language = get_language()

    with force_language(language):
        absolute_url = obj.get_absolute_url()
        if not absolute_url:
            return None
        url_param = get_cms_setting("ENDPOINT_LIVE_URL_QUERYSTRING_PARAM")
        if params and url_param in params:
            params = params.copy()
            del params[url_param]
        if params and "?" not in absolute_url:
            absolute_url = absolute_url + "?" + params.urlencode()

    obj_site = getattr(obj, 'site', None)
    if obj_site is None:
        try:
            grouper_field = apps.get_app_config('cms').cms_extension.model_groupers[obj.__class__]
            obj_site = getattr(getattr(obj, grouper_field, None), 'site', None)
        except KeyError:
            pass
    if obj_site and obj_site != site:
        # Add domain if current and target sites are defined and different
        absolute_url = f"//{obj_site.domain}{absolute_url}"

    return absolute_url


def select_grouper(queryset: models.QuerySet) -> models.QuerySet:
    """Join the grouper registered for the queryset's model, if there is one.

    Content models name their grouper in ``cms_toolbar_enabled_models`` (pages:
    ``"page"``). The toolbar and the editor read it for nearly every object they
    load, so fetching it along saves a query per request -- for any registered
    model, not only page content. Only a forward foreign key or one-to-one field
    can be joined; any other grouper leaves the queryset as it is.
    """
    field_name = apps.get_app_config("cms").cms_extension.model_groupers.get(queryset.model)
    if not field_name:
        return queryset
    try:
        field = queryset.model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return queryset
    if (field.many_to_one or field.one_to_one) and field.concrete:
        return queryset.select_related(field_name)
    return queryset


def get_object_for_language(obj: models.Model, language: str, latest: bool = False) -> models.Model | None:
    """
    Retrieves the correct content object for the target language. The object must be frontend-editable
    and registered as such with cms.

    Two cases have to be distinguished:

    1. **Object has a language property:** If the language of the passed object is different,
       sibling objects are retrieved from the database and cached in the object passed.
    2. **Object has no language property:** The placeholders of the object contain the different
       language content. The object itself is returned
    """
    if getattr(obj, "language", language) == language:
        # Object does not have language field or language is requested language
        # Return object itself
        return obj
    # TODO(cms6): pages-specific fast path; becomes a registered hook so that
    # `shared` stops reaching into a container. Tracked in .importlinter.
    from cms.models import PageContent

    if isinstance(obj, PageContent):
        return obj.page.get_admin_content(language, fallback=False) or None
    # Does the object have a cache with sister objects
    cached_object = getattr(obj, "_sibling_objects_for_language_cache", {})
    if cached_object:
        return cached_object.get(language)

    extension = apps.get_app_config('cms').cms_extension
    model = obj.__class__
    field = extension.model_groupers.get(model)
    if not field:
        # Cannot infer sister object if grouper field is unknown
        return None
    # Grouper model not registered or does not have a get_content_obj method,
    # or get_content_obj does not accept language parameter
    # Now query db
    grouper_filter = {field: getattr(obj, field)}
    qs = model.admin_manager.latest_content() if latest and hasattr(model, "admin_manager") else model.objects
    obj._sibling_objects_for_language_cache = {
        result.language: result for result in qs.filter(**grouper_filter)
    }
    return obj._sibling_objects_for_language_cache.get(language)
