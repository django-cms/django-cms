"""The frontend editor's endpoints, generic over whatever model is being edited.

A model becomes editable by registering in its ``cms_config.py``
(``cms_toolbar_enabled_models``); nothing here knows about pages, blog posts or
anything else in particular. Where a container needs to do something special --
prefetch differently, apply its own view permission, hand off to an apphook --
it registers a hook with :mod:`cms.shared.resolvers` rather than being
special-cased here. Pages does exactly that in :mod:`cms.pages.editing`.

Moved from ``cms.views``, which keeps the page-serving views.
"""

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.template.defaultfilters import title
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch

from cms.core.permissions import user_can_view_placeholder_source
from cms.core.placeholders import get_declared_placeholders_for_obj, get_placeholder_conf
from cms.shared.editing_urls import get_object_preview_url
from cms.shared.resolvers import resolve
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils import get_current_site
from cms.utils.helpers import is_editable_model

__all__ = [
    "render_object_edit",
    "render_object_endpoint",
    "render_object_preview",
    "render_object_structure",
    "render_placeholder_content",
]


def _content_type_or_404(content_type_id) -> ContentType:
    try:
        return ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist as err:
        raise Http404 from err


def _load_object(content_type: ContentType, object_id, request):
    """Fetch the object being edited.

    A container may answer with its own query -- pages prefetches the page and
    its site, and records it on the request -- otherwise the generic lookup runs.
    """
    obj = resolve("editing_object", content_type=content_type, object_id=object_id, request=request)
    if obj is not None:
        return obj
    return content_type.get_object_for_this_type(pk=object_id)


def _may_view(user, obj) -> bool:
    """Whether ``user`` may look at ``obj`` in the editor.

    Viewing requires only view permission; mutations stay gated by change
    permission at the plugin endpoints. A container may answer for its own
    models -- pages applies its page-view rules -- otherwise the placeholder
    source check applies.
    """
    answer = resolve("editing_can_view", user=user, obj=obj)
    if answer is None:
        return user_can_view_placeholder_source(user, obj)
    return answer


def render_object_structure(request, content_type_id, object_id):
    content_type = _content_type_or_404(content_type_id)
    try:
        obj = _load_object(content_type, object_id, request)
        if not _may_view(request.user, obj):
            raise Http404
    except ObjectDoesNotExist as err:
        raise Http404 from err

    context = {"object": obj, "cms_toolbar": request.toolbar}
    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(obj)
    return render(request, "cms/toolbar/structure.html", context)


def render_placeholder_content(request, obj, context):
    context["cms_placeholder_slots"] = (
        (
            placeholder.slot,
            get_placeholder_conf("name", placeholder.slot, default=title(placeholder.slot)),
            placeholder.inherit,
        )
        for placeholder in get_declared_placeholders_for_obj(obj)
    )
    return TemplateResponse(request, "cms/headless/placeholder.html", context)


def render_object_endpoint(request, content_type_id, object_id, require_editable):
    content_type = _content_type_or_404(content_type_id)
    model = content_type.model_class()

    if require_editable and not is_editable_model(model):
        return HttpResponseBadRequest("Requested object does not support frontend rendering")

    try:
        obj = _load_object(content_type, object_id, request)

        # A container may serve this object through a URL of its own -- a page
        # with an apphook attached is served by the apphook's view, not by the
        # editor. It answers with a response when it takes over.
        handled = resolve(
            "editing_alternate_response", obj=obj, request=request, editable=require_editable
        )
        if handled is not None:
            return handled

        if not _may_view(request.user, obj):
            raise Http404
    except ObjectDoesNotExist as err:
        raise Http404 from err

    # Resolve current_page from the object's own URL, so that an object served
    # under an apphook still knows which page it hangs below.
    if not getattr(request, "current_page", None):
        try:
            object_url = obj.get_absolute_url()
        except (AttributeError, NoReverseMatch):
            object_url = None

        if object_url:
            request.current_page = resolve(
                "editing_page_for_url", url=object_url, request=request
            )

    extension = apps.get_app_config("cms").cms_extension

    if model not in extension.toolbar_enabled_models:
        return HttpResponseBadRequest("Requested object does not support frontend rendering")

    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(obj)
    request.site = get_current_site(request)

    redirect = getattr(obj, "redirect", None)
    if isinstance(redirect, str):
        toolbar.redirect_url = redirect

    if require_editable and not toolbar.object_is_editable():
        # If not editable, switch from edit to preview endpoint
        return HttpResponseRedirect(get_object_preview_url(obj))

    render_func = extension.toolbar_enabled_models[model]
    return render_func(request, obj)


def render_object_edit(request, content_type_id, object_id):
    return render_object_endpoint(request, content_type_id, object_id, require_editable=True)


def render_object_preview(request, content_type_id, object_id):
    return render_object_endpoint(request, content_type_id, object_id, require_editable=False)
