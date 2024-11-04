from urllib.parse import quote

from django.apps import apps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.urls import Resolver404, resolve, reverse
from django.utils.cache import patch_cache_control
from django.utils.timezone import now
from django.utils.translation import activate, get_language_from_request
from django.views.decorators.http import require_POST

from cms.apphook_pool import apphook_pool
from cms.cache.page import get_page_cache
from cms.exceptions import LanguageError
from cms.forms.login import CMSToolbarLoginForm
from cms.models import PageContent
from cms.models.pagemodel import TreeNode
from cms.page_rendering import (
    _handle_no_apphook,
    _handle_no_page,
    _render_welcome_page,
    render_pagecontent,
)
from cms.toolbar.utils import get_object_preview_url, get_toolbar_from_request
from cms.utils import get_current_site
from cms.utils.compat import DJANGO_2_2, DJANGO_3_0, DJANGO_3_1
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import is_editable_model
from cms.utils.i18n import (
    get_default_language_for_site,
    get_fallback_languages,
    get_language_list,
    get_public_languages,
    get_redirect_on_fallback,
    is_language_prefix_patterns_used,
)
from cms.utils.page import get_page_from_request

if DJANGO_2_2:
    from django.utils.http import (
        is_safe_url as url_has_allowed_host_and_scheme,
    )
else:
    from django.utils.http import url_has_allowed_host_and_scheme


def _clean_redirect_url(redirect_url, language):
    if (redirect_url and is_language_prefix_patterns_used() and redirect_url[0] == "/" and not redirect_url.startswith(
            f"/{language}/"
    )):
        # add language prefix to url
        redirect_url = f"/{language}/{redirect_url.lstrip('/')}"
    return redirect_url


def details(request, slug):
    """
    The main view of the Django-CMS! Takes a request and a slug, renders the
    page.
    """
    is_authenticated = request.user.is_authenticated
    response_timestamp = now()
    if get_cms_setting("PAGE_CACHE") and (
        not hasattr(request, 'toolbar') or (
            not request.toolbar.edit_mode_active and not request.toolbar.show_toolbar and not is_authenticated
        )
    ):
        cache_content = get_page_cache(request)
        if cache_content is not None:
            content, headers, expires_datetime = cache_content
            response = HttpResponse(content)
            response.xframe_options_exempt = True
            if DJANGO_2_2 or DJANGO_3_0 or DJANGO_3_1:
                response._headers = headers
            else:
                #  for django3.2 and above. response.headers replaces response._headers in earlier versions of django
                response.headers = headers
            # Recalculate the max-age header for this cached response
            max_age = int(
                (expires_datetime - response_timestamp).total_seconds() + 0.5)
            patch_cache_control(response, max_age=max_age)
            return response

    # Get a Page model object from the request
    site = get_current_site()
    page = get_page_from_request(request, use_path=slug)
    tree_nodes = TreeNode.objects.get_for_site(site)

    if not page and not slug and not tree_nodes.exists():
        # render the welcome page if the requested path is root "/"
        # and there's no pages
        return _render_welcome_page(request)

    if not page and get_cms_setting("REDIRECT_TO_LOWERCASE_SLUG"):
        # Redirect to the lowercase version of the slug
        if slug.lower() != slug:
            # Only redirect if the slug changes
            redirect_url = reverse("pages-details-by-slug", kwargs={"slug": slug.lower()})
            if get_cms_setting('REDIRECT_PRESERVE_QUERY_PARAMS'):
                query_string = request.META.get('QUERY_STRING')
                if query_string:
                    redirect_url += "?" + query_string
            return HttpResponseRedirect(redirect_url)

    if not page:
        # raise 404 or redirect to PageContent's
        # changelist in the admin if this is a
        # request to the root URL
        return _handle_no_page(request)

    request.current_page = page

    if hasattr(request, 'user') and request.user.is_staff:
        user_languages = get_language_list(site_id=site.pk)
    else:
        user_languages = get_public_languages(site_id=site.pk)

    request_language = None
    if is_language_prefix_patterns_used():
        request_language = get_language_from_request(request, check_path=True)
    if not request_language:
        request_language = get_default_language_for_site(get_current_site().pk)

    if not page.is_home and request_language not in user_languages:
        # The homepage is treated differently because
        # when a request goes to the root of the site (/)
        # without a language, Django will redirect to the user's
        # browser language which might not be a valid cms language,
        # this means we need to correctly redirect that request.
        return _handle_no_page(request)

    # we use the _get_page_content_cache method to populate the cache with all public languages
    # The languages are then filtered out by the user allowed languages
    page._get_page_content_cache(None, fallback=True, force_reload=True)
    pagecontent_languages = list(page.page_content_cache.keys())
    available_languages = [
        language for language in user_languages
        if language in pagecontent_languages
    ]

    own_urls = [
        request.build_absolute_uri(request.path),
        '/%s' % request.path,
        request.path,
    ]

    try:
        redirect_on_fallback = get_redirect_on_fallback(request_language, site_id=site.pk)
    except LanguageError:
        redirect_on_fallback = False

    if request_language not in user_languages:
        # Language is not allowed
        # Use the default site language
        default_language = get_default_language_for_site(site.pk)
        fallbacks = get_fallback_languages(default_language, site_id=site.pk)
        fallbacks = [default_language] + fallbacks
    else:
        fallbacks = get_fallback_languages(request_language, site_id=site.pk)

    # Only fallback to languages the user is allowed to see
    fallback_languages = [
        language for language in fallbacks
        if language != request_language and language in available_languages
    ]
    language_is_unavailable = request_language not in available_languages
    first_fallback_language = next(iter(fallback_languages or []), None)

    if language_is_unavailable and not fallback_languages:
        # There is no page with the requested language
        # and there's no configured fallbacks
        return _handle_no_page(request)
    elif language_is_unavailable and redirect_on_fallback:
        # There is no page with the requested language and
        # redirect_on_fallback is True,
        # so redirect to the first configured / available fallback language
        redirect_url = page.get_absolute_url(
            first_fallback_language, fallback=False)
    else:
        page_path = page.get_absolute_url(request_language)
        page_slug = page.get_path(request_language) or page.get_slug(request_language)

        if slug and slug != page_slug and request.path[:len(page_path)] != page_path:
            # The current language does not match its slug.
            # Redirect to the current language.
            return HttpResponseRedirect(page_path)
        # Check if the page has a redirect url defined for this language.
        redirect_url = page.get_redirect(request_language, fallback=False) or ''
        redirect_url = _clean_redirect_url(redirect_url, request_language)

    if redirect_url:
        if redirect_url not in own_urls:
            if get_cms_setting('REDIRECT_PRESERVE_QUERY_PARAMS'):
                query_string = request.META.get('QUERY_STRING')
                if query_string:
                    redirect_url += "?" + query_string
            # prevent redirect to self
            return HttpResponseRedirect(redirect_url)

    # permission checks
    if page.login_required and not request.user.is_authenticated:
        return redirect_to_login(quote(request.get_full_path()), settings.LOGIN_URL)

    content_language = request_language
    if language_is_unavailable:
        # When redirect_on_fallback is False and
        # language is unavailable, render the content
        # in the first fallback language available
        # by switching to it
        content_language = first_fallback_language
        # translation.activate() is used without context
        # as the context won't be preserved when the
        # plugins get rendered
        activate(content_language)

    content = page.get_content_obj(language=content_language)
    # use the page object with populated cache
    content.page = page
    if hasattr(request, 'toolbar'):
        request.toolbar.set_object(content)

    return render_pagecontent(request, content)


@require_POST
def login(request):
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME)

    if not url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts=request.get_host()):
        redirect_to = reverse("pages-root")
    else:
        redirect_to = quote(redirect_to)

    if request.user.is_authenticated:
        return HttpResponseRedirect(redirect_to)

    form = CMSToolbarLoginForm(request=request, data=request.POST)

    if form.is_valid():
        auth_login(request, form.user_cache)
    else:
        redirect_to += '?cms_toolbar_login_error=1'
    return HttpResponseRedirect(redirect_to)


def render_object_structure(request, content_type_id, object_id):
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist as err:
        raise Http404 from err

    try:
        content_type_obj = content_type.get_object_for_this_type(pk=object_id)
    except ObjectDoesNotExist as err:
        raise Http404 from err

    context = {
        'object': content_type_obj,
        'cms_toolbar': request.toolbar,
    }
    if isinstance(content_type_obj, PageContent):
        request.current_page = content_type_obj.page
    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(content_type_obj)
    return render(request, 'cms/toolbar/structure.html', context)


def render_object_endpoint(request, content_type_id, object_id, require_editable):
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist as err:
        raise Http404 from err
    else:
        model = content_type.model_class()

    if require_editable and not is_editable_model(model):
        return HttpResponseBadRequest('Requested object does not support frontend rendering')

    try:
        if issubclass(model, PageContent):
            # An apphook might be attached to a PageContent object
            content_type_obj = model.admin_manager.select_related("page").get(pk=object_id)
            request.current_page = content_type_obj.page
            if (
                content_type_obj.page.application_urls and  # noqa: W504
                content_type_obj.page.application_urls in dict(apphook_pool.get_apphooks())
            ):
                try:
                    # If so, try get the absolute URL and pass it to the toolbar as request_path
                    # The apphook's view function will be called.
                    absolute_url = content_type_obj.get_absolute_url()
                    from cms.toolbar.toolbar import CMSToolbar
                    request.toolbar = CMSToolbar(request, request_path=absolute_url)
                    # Resolve the apphook's url to get its view function
                    view_func, args, kwargs = resolve(absolute_url)
                    if view_func is not details:
                        return view_func(request, *args, **kwargs)
                except Resolver404:
                    # Apphook does not provide a view for its "root", show warning message
                    return _handle_no_apphook(request)
        else:
            content_type_obj = content_type.get_object_for_this_type(pk=object_id)
    except ObjectDoesNotExist as err:
        raise Http404 from err

    extension = apps.get_app_config('cms').cms_extension

    if model not in extension.toolbar_enabled_models:
        return HttpResponseBadRequest('Requested object does not support frontend rendering')

    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(content_type_obj)

    if request.user.is_staff and toolbar.edit_mode_active:
        redirect = getattr(content_type_obj, "redirect", None)
        if isinstance(redirect, str):
            toolbar.redirect_url = redirect

    if require_editable and not toolbar.object_is_editable():
        # If not editable, switch from edit to preview endpoint
        return HttpResponseRedirect(get_object_preview_url(content_type_obj))

    render_func = extension.toolbar_enabled_models[model]
    return render_func(request, content_type_obj)


def render_object_edit(request, content_type_id, object_id):
    return render_object_endpoint(request, content_type_id, object_id, require_editable=True)


def render_object_preview(request, content_type_id, object_id):
    return render_object_endpoint(request, content_type_id, object_id, require_editable=False)
