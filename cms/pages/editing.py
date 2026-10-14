"""How pages take part in the frontend editor.

The editor (:mod:`cms.core.editing.views`) is generic; these hooks are how the
pages container gets the things it needs that a plain editable model does not:
a prefetched query, its own view permission, apphook hand-off, page resolution
from a URL, and the page a toolbar requested by the toolbar endpoint belongs to. Registered with :mod:`cms.shared.resolvers` so that core
never imports pages.

Imported from ``cms.cms_config`` so the registrations run at app startup.
"""

from cms.models import Page, PageContent
from cms.pages.apphook_pool import apphook_pool
from cms.pages.appresolver import applications_page_check
from cms.pages.utils import get_page_from_request
from cms.permissions.page_permissions import user_can_view_page
from cms.shared.resolvers import provide


def _editing_object(content_type, object_id, request):
    """Fetch a page content object with its page and site, and record the page.

    ``request.current_page`` has to be set before anything renders, and fetching
    page and site together saves the editor two queries per request. Returns
    ``None`` for anything that is not page content, letting the generic lookup
    handle it.
    """
    model = content_type.model_class()
    if not issubclass(model, PageContent):
        return None

    # ``admin_manager`` so that a versioning package's filtering does not hide
    # the very draft the editor was asked to open.
    obj = model.admin_manager.select_related("page", "page__site").get(pk=object_id)
    request.current_page = obj.page
    return obj


def _editing_can_view(user, obj):
    """Page content follows page view permission, not placeholder-source rules.

    Without this a staff user who may not view a restricted page could still
    read its plugin structure through the editor endpoints. A page itself is
    asked about by the toolbar endpoint when no object is attached.
    """
    if isinstance(obj, Page):
        return user_can_view_page(user, obj)
    if not isinstance(obj, PageContent):
        return None
    return user_can_view_page(user, obj.page)


def _editing_alternate_response(obj, request, editable):
    """Hand off to an apphook's view when the page has one attached.

    A page with an apphook is served by the apphook, so the editor renders what
    the visitor would actually see rather than an empty page shell.
    """
    if not isinstance(obj, PageContent):
        return None

    page = obj.page
    if not page.application_urls or page.application_urls not in dict(apphook_pool.get_apphooks()):
        return None
    if editable and not obj.is_editable(request):
        return None

    from django.urls import Resolver404, resolve as resolve_url
    from django.utils.translation import override

    from cms.pages.rendering import _handle_no_apphook
    from cms.toolbar.toolbar import CMSToolbar
    from cms.views import details

    try:
        # The editor endpoint may be called in another language than the edited
        # translation (an admin running in English, say). The apphook's URLs are
        # resolved per language, so resolve and render in the translation's.
        with override(obj.language):
            # Point the toolbar at the URL the visitor would use, not the endpoint.
            absolute_url = obj.get_absolute_url()
            request.toolbar = CMSToolbar(request, request_path=absolute_url)
            # Make the page content's placeholders available; the apphook view may
            # overwrite this with an object of its own.
            request.toolbar.set_object(obj)
            view_func, args, kwargs = resolve_url(absolute_url)
            if view_func is not details:
                return view_func(request, *args, **kwargs)
    except Resolver404:
        # Apphook provides no view for its root; show the warning page.
        return _handle_no_apphook(request)
    return None


def _editing_page_for_url(url, request):
    """Which page serves ``url``, if any -- used for objects under an apphook."""
    original_path_info = request.path_info
    try:
        request.path_info = url
        return applications_page_check(request)
    finally:
        request.path_info = original_path_info


def _toolbar_current_page(request, obj, path):
    """The page a toolbar requested through the toolbar endpoint belongs to.

    The attached object's own page if it is page content, otherwise the page
    served at ``path`` (the page the toolbar is shown on).
    """
    if isinstance(obj, PageContent):
        return obj.page
    return get_page_from_request(request, use_path=path, clean_path=True)


provide("editing_object", _editing_object)
provide("editing_can_view", _editing_can_view)
provide("editing_alternate_response", _editing_alternate_response)
provide("editing_page_for_url", _editing_page_for_url)
provide("toolbar_current_page", _toolbar_current_page)
