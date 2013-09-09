# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_urls
from cms.models import Title
from cms.utils import get_template_from_request, get_language_from_request
from cms.utils.i18n import (
    force_language,
    get_public_languages,
    get_languages_for_page_user,
    get_languages_for_user,
    get_redirect_on_fallback,
    is_language_prefix_patterns_used,
)
from cms.utils.page_resolver import get_fallback_languages_for_page, get_page_from_request
from cms.test_utils.util.context_managers import SettingsOverride

from django.conf import settings
from django.conf.urls.defaults import patterns
from django.core.urlresolvers import resolve, Resolver404, reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib.auth.views import redirect_to_login
from django.utils.http import urlquote


def _handle_no_page(request, slug):
    if not slug and settings.DEBUG:
        return render_to_response("cms/new.html", RequestContext(request))
    raise Http404('CMS: Page not found for "%s"' % slug)


def details(request, slug):
    """
    The main view of the Django-CMS! Takes a request and a slug, renders the
    page.
    """
    # get the right model
    context = RequestContext(request)
    # Get a Page model object from the request
    page = get_page_from_request(request, use_path=slug)

    if not page:
        return _handle_no_page(request, slug)

    current_language = get_language_from_request(request)

    # Languages specific to page that the current user can see.
    available_languages = get_languages_for_page_user(page=page, user=request.user)

    attrs = ''
    if 'edit' in request.GET:
        attrs = '?edit=1'
    elif 'preview' in request.GET:
        attrs = '?preview=1'
        if 'draft' in request.GET:
            attrs += '&draft=1'

    # Check that the user has access to this language
    # which is defined in FRONTEND_LANGUAGES:
    if not current_language in get_languages_for_user(user=request.user):
        #are we on root?
        if not slug and available_languages:
            #redirect to supported language
            languages = [(language, language) for language in available_languages]
            with SettingsOverride(LANGUAGES=languages, LANGUAGE_CODE=languages[0][0]):
                # get supported language
                new_language = get_language_from_request(request)
                if new_language in get_public_languages():
                    with force_language(new_language):
                        pages_root = reverse('pages-root')
                        return HttpResponseRedirect(pages_root + attrs)
        else:
            return _handle_no_page(request, slug)

    if current_language not in available_languages:
        fallback_languages = get_fallback_languages_for_page(page, current_language, request.user)
        if fallback_languages:
            if get_redirect_on_fallback(current_language):
                fallback_language = fallback_languages[0]
                with force_language(fallback_language):
                    path = page.get_absolute_url(language=fallback_language, fallback=True) + attrs
                    return HttpResponseRedirect(path)
        else:
            # There is a page object we can't find a proper language to render it
            return _handle_no_page(request, slug)
    else:
        page_path = page.get_absolute_url(language=current_language)
        page_slug = page.get_path(language=current_language) or page.get_slug(language=current_language)
        if slug and slug != page_slug and request.path[:len(page_path)] != page_path:
            # The current language does not match it's slug.
            # Redirect to the current language.
            return HttpResponseRedirect(page_path + attrs)

    if apphook_pool.get_apphooks():
        # There are apphooks in the pool. Let's see if there is one for the
        # current page
        # since we always have a page at this point, applications_page_check is
        # pointless
        # page = applications_page_check(request, page, slug)
        # Check for apphooks! This time for real!
        try:
            app_urls = page.get_application_urls(current_language, False)
        except Title.DoesNotExist:
            app_urls = []
        if app_urls:
            app = apphook_pool.get_apphook(app_urls)
            pattern_list = []
            for urlpatterns in get_app_urls(app.urls):
                pattern_list += urlpatterns
            urlpatterns = patterns('', *pattern_list)
            try:
                context.current_app = page.reverse_id if page.reverse_id else app.app_name
                view, args, kwargs = resolve('/', tuple(urlpatterns))
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
        own_urls = [
            'http%s://%s%s' % ('s' if request.is_secure() else '', request.get_host(), request.path),
            '/%s' % request.path,
            request.path,
        ]
        if redirect_url not in own_urls:
            return HttpResponseRedirect(redirect_url + attrs)

    # permission checks
    if page.login_required and not request.user.is_authenticated():
        return redirect_to_login(urlquote(request.get_full_path()), settings.LOGIN_URL)

    template_name = get_template_from_request(request, page, no_current_page=True)

    has_view_permissions = page.has_view_permission(request)

    # fill the context
    context['lang'] = current_language
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    context['has_view_permissions'] = has_view_permissions

    if not has_view_permissions:
        return _handle_no_page(request, slug)
    return render_to_response(template_name, context_instance=context)
