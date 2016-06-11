# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import resolve, Resolver404, reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.cache import patch_cache_control
from django.utils.http import urlquote
from django.utils.timezone import now
from django.utils.translation import get_language

from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_urls
from cms.cache.page import get_page_cache
from cms.page_rendering import _handle_no_page, render_page
from cms.utils import get_language_code, get_language_from_request, get_cms_setting
from cms.utils.i18n import (get_fallback_languages, force_language, get_public_languages,
                            get_redirect_on_fallback, get_language_list,
                            is_language_prefix_patterns_used)
from cms.utils.page_resolver import get_page_from_request


def details(request, slug):
    """
    The main view of the Django-CMS! Takes a request and a slug, renders the
    page.
    """
    response_timestamp = now()
    if get_cms_setting("PAGE_CACHE") and (
        not hasattr(request, 'toolbar') or (
            not request.toolbar.edit_mode and
            not request.toolbar.show_toolbar and
            not request.user.is_authenticated()
        )
    ):
        cache_content = get_page_cache(request)
        if cache_content is not None:
            content, headers, expires_datetime = cache_content
            response = HttpResponse(content)
            response._headers = headers
            # Recalculate the max-age header for this cached response
            max_age = int(
                (expires_datetime - response_timestamp).total_seconds() + 0.5)
            patch_cache_control(response, max_age=max_age)
            return response

    # Get a Page model object from the request
    page = get_page_from_request(request, use_path=slug)
    if not page:
        return _handle_no_page(request, slug)
    current_language = request.GET.get('language', None)
    if not current_language:
        current_language = request.POST.get('language', None)
    if current_language:
        current_language = get_language_code(current_language)
        if current_language not in get_language_list(page.site_id):
            current_language = None
    if current_language is None:
        current_language = get_language_code(getattr(request, 'LANGUAGE_CODE', None))
        if current_language:
            current_language = get_language_code(current_language)
            if current_language not in get_language_list(page.site_id):
                current_language = None
    if current_language is None:
        current_language = get_language_code(get_language())
    # Check that the current page is available in the desired (current) language
    available_languages = []
    # this will return all languages in draft mode, and published only in live mode
    page_languages = list(page.get_published_languages())
    if hasattr(request, 'user') and request.user.is_staff:
        user_languages = get_language_list()
    else:
        user_languages = get_public_languages()
    for frontend_lang in user_languages:
        if frontend_lang in page_languages:
            available_languages.append(frontend_lang)
    # Check that the language is in FRONTEND_LANGUAGES:
    own_urls = [
        'http%s://%s%s' % ('s' if request.is_secure() else '', request.get_host(), request.path),
        '/%s' % request.path,
        request.path,
    ]
    if current_language not in user_languages:
        #are we on root?
        if not slug:
            #redirect to supported language
            languages = []
            for language in available_languages:
                languages.append((language, language))
            if languages:
                # get supported language
                new_language = get_language_from_request(request)
                if new_language in get_public_languages():
                    with force_language(new_language):
                        pages_root = reverse('pages-root')
                        if (hasattr(request, 'toolbar') and request.user.is_staff and request.toolbar.edit_mode):
                            request.toolbar.redirect_url = pages_root
                        elif pages_root not in own_urls:
                            return HttpResponseRedirect(pages_root)
            elif not hasattr(request, 'toolbar') or not request.toolbar.redirect_url:
                _handle_no_page(request, slug)
        else:
            return _handle_no_page(request, slug)
    if current_language not in available_languages:
        # If we didn't find the required page in the requested (current)
        # language, let's try to find a fallback
        found = False
        for alt_lang in get_fallback_languages(current_language):
            if alt_lang in available_languages:
                if get_redirect_on_fallback(current_language) or slug == "":
                    with force_language(alt_lang):
                        path = page.get_absolute_url(language=alt_lang, fallback=True)
                        # In the case where the page is not available in the
                    # preferred language, *redirect* to the fallback page. This
                    # is a design decision (instead of rendering in place)).
                    if (hasattr(request, 'toolbar') and request.user.is_staff
                            and request.toolbar.edit_mode):
                        request.toolbar.redirect_url = path
                    elif path not in own_urls:
                        return HttpResponseRedirect(path)
                else:
                    found = True
        if not found and (not hasattr(request, 'toolbar') or not request.toolbar.redirect_url):
            # There is a page object we can't find a proper language to render it
            _handle_no_page(request, slug)
    else:
        page_path = page.get_absolute_url(language=current_language)
        page_slug = page.get_path(language=current_language) or page.get_slug(language=current_language)

        if slug and slug != page_slug and request.path[:len(page_path)] != page_path:
            # The current language does not match it's slug.
            #  Redirect to the current language.
            if hasattr(request, 'toolbar') and request.user.is_staff and request.toolbar.edit_mode:
                request.toolbar.redirect_url = page_path
            else:
                return HttpResponseRedirect(page_path)

    if apphook_pool.get_apphooks():
        # There are apphooks in the pool. Let's see if there is one for the
        # current page
        # since we always have a page at this point, applications_page_check is
        # pointless
        # page = applications_page_check(request, page, slug)
        # Check for apphooks! This time for real!
        app_urls = page.get_application_urls(current_language, False)
        skip_app = False
        if (not page.is_published(current_language) and hasattr(request, 'toolbar')
                and request.toolbar.edit_mode):
            skip_app = True
        if app_urls and not skip_app:
            app = apphook_pool.get_apphook(app_urls)
            pattern_list = []
            if app:
                for urlpatterns in get_app_urls(app.get_urls(page, current_language)):
                    pattern_list += urlpatterns
                try:
                    view, args, kwargs = resolve('/', tuple(pattern_list))
                    return view(request, *args, **kwargs)
                except Resolver404:
                    pass
    # Check if the page has a redirect url defined for this language.
    redirect_url = page.get_redirect(language=current_language)
    if redirect_url:
        if (is_language_prefix_patterns_used() and redirect_url[0] == "/"
                and not redirect_url.startswith('/%s/' % current_language)):
            # add language prefix to url
            redirect_url = "/%s/%s" % (current_language, redirect_url.lstrip("/"))
            # prevent redirect to self

        if hasattr(request, 'toolbar') and request.user.is_staff and request.toolbar.edit_mode:
            request.toolbar.redirect_url = redirect_url
        elif redirect_url not in own_urls:
            return HttpResponseRedirect(redirect_url)

    # permission checks
    if page.login_required and not request.user.is_authenticated():
        return redirect_to_login(urlquote(request.get_full_path()), settings.LOGIN_URL)
    if hasattr(request, 'toolbar'):
        request.toolbar.set_object(page)

    response = render_page(request, page, current_language=current_language, slug=slug)
    return response
