from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_cache_control
from urllib.parse import quote
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import now
from django.utils.translation import get_language_from_request
from django.views.decorators.http import require_POST

from cms.cache.page import get_page_cache
from cms.exceptions import LanguageError
from cms.forms.login import CMSToolbarLoginForm
from cms.models.pagemodel import TreeNode
from cms.page_rendering import _handle_no_page, _render_welcome_page, render_pagecontent
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils import get_current_site
from cms.utils.compat import DJANGO_2_2, DJANGO_3_0, DJANGO_3_1
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import is_editable_model
from cms.utils.i18n import (get_fallback_languages, get_public_languages,
                            get_redirect_on_fallback, get_language_list,
                            get_default_language_for_site,
                            is_language_prefix_patterns_used)
from cms.utils.page import get_page_from_request


def _clean_redirect_url(redirect_url, language):
    if (redirect_url and is_language_prefix_patterns_used() and redirect_url[0] == "/"
            and not redirect_url.startswith('/%s/' % language)):
        # add language prefix to url
        redirect_url = "/%s/%s" % (language, redirect_url.lstrip("/"))
    return redirect_url


def details(request, slug):
    """
    The main view of the Django-CMS! Takes a request and a slug, renders the
    page.
    """
    response_timestamp = now()
    if get_cms_setting("PAGE_CACHE") and (
        not hasattr(request, 'toolbar') or (
            not request.toolbar.edit_mode_active and
            not request.toolbar.show_toolbar and
            not request.user.is_authenticated
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
    toolbar = get_toolbar_from_request(request)
    tree_nodes = TreeNode.objects.get_for_site(site)

    if not page and not slug and not tree_nodes.exists():
        # render the welcome page if the requested path is root "/"
        # and there's no pages
        return _render_welcome_page(request)

    if not page:
        # raise 404
        _handle_no_page(request)

    request.current_page = page

    if hasattr(request, 'user') and request.user.is_staff:
        user_languages = get_language_list(site_id=site.pk)
    else:
        user_languages = get_public_languages(site_id=site.pk)

    request_language = get_language_from_request(request, check_path=True)

    if not page.is_home and request_language not in user_languages:
        # The homepage is treated differently because
        # when a request goes to the root of the site (/)
        # without a language, Django will redirect to the user's
        # browser language which might not be a valid cms language,
        # this means we need to correctly redirect that request.
        return _handle_no_page(request)

    # get_published_languages will return all languages in draft mode
    # and published only in live mode.
    # These languages are then filtered out by the user allowed languages
    available_languages = [
        language for language in user_languages
        if language in list(page.get_languages())
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

    if language_is_unavailable and not fallback_languages:
        # There is no page with the requested language
        # and there's no configured fallbacks
        return _handle_no_page(request)
    elif language_is_unavailable and (redirect_on_fallback or page.is_home):
        # There is no page with the requested language and
        # the user has explicitly requested to redirect on fallbacks,
        # so redirect to the first configured / available fallback language
        fallback = fallback_languages[0]
        redirect_url = page.get_absolute_url(fallback, fallback=False)
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
        if request.user.is_staff and toolbar.edit_mode_active:
            toolbar.redirect_url = redirect_url
        elif redirect_url not in own_urls:
            # prevent redirect to self
            return HttpResponseRedirect(redirect_url)

    # permission checks
    if page.login_required and not request.user.is_authenticated:
        return redirect_to_login(quote(request.get_full_path()), settings.LOGIN_URL)

    content = page.get_title_obj(language=request_language)
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
        redirect_to += u'?cms_toolbar_login_error=1'
    return HttpResponseRedirect(redirect_to)


def render_object_structure(request, content_type_id, object_id):
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist:
        raise Http404

    try:
        content_type_obj = content_type.get_object_for_this_type(pk=object_id)
    except ObjectDoesNotExist:
        raise Http404

    context = {
        'object': content_type_obj,
        'cms_toolbar': request.toolbar,
    }
    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(content_type_obj)
    return render(request, 'cms/toolbar/structure.html', context)


def render_object_edit(request, content_type_id, object_id):
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist:
        raise Http404
    else:
        model = content_type.model_class()

    if not is_editable_model(model):
        return HttpResponseBadRequest('Requested object does not support frontend rendering')

    try:
        content_type_obj = content_type.get_object_for_this_type(pk=object_id)
    except ObjectDoesNotExist:
        raise Http404

    extension = apps.get_app_config('cms').cms_extension

    if model not in extension.toolbar_enabled_models:
        return HttpResponseBadRequest('Requested object does not support frontend rendering')

    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(content_type_obj)
    render_func = extension.toolbar_enabled_models[model]
    return render_func(request, content_type_obj)


def render_object_preview(request, content_type_id, object_id):
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist:
        raise Http404
    else:
        model = content_type.model_class()

    try:
        content_type_obj = content_type.get_object_for_this_type(pk=object_id)
    except ObjectDoesNotExist:
        raise Http404

    extension = apps.get_app_config('cms').cms_extension

    if model not in extension.toolbar_enabled_models:
        return HttpResponseBadRequest('Requested object does not support frontend rendering')

    toolbar = get_toolbar_from_request(request)
    toolbar.set_object(content_type_obj)
    render_func = extension.toolbar_enabled_models[model]
    return render_func(request, content_type_obj)
