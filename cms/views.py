# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import Resolver404
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.cache import patch_cache_control
from django.utils.translation import get_language
from django.utils.http import urlquote
from django.utils.timezone import now
from django.views.generic import View

from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_response_for_page
from cms.cache.page import get_page_cache
from cms.page_rendering import _handle_no_page, render_page
from cms.utils import get_language_from_request, get_cms_setting, get_desired_language
from cms.utils.i18n import (get_fallback_languages, get_public_languages,
                            get_redirect_on_fallback, complete_i18n_url,
                            get_language_code, get_visible_languages)
from cms.utils.page_resolver import get_page_from_request


class CircularRedirectionError(Exception):
    pass


def details(request, slug):
    view = PageView.as_view()
    return view(request, slug)


class PageView(View):
    """
    The main view of the Django-CMS! Takes a request and a slug,
    renders the page.
    """
    RESPONSE_ATTEMPTS = [
        'get_404_response_or_none',
        'get_redirect_away_from_root_or_none',
        'get_redirect_to_fallback_language_or_404_or_none',
        'get_redirect_to_proper_slug_or_none',
        'get_apphook_response_or_none',
        'get_cms_redirection_or_none',
        'get_redirect_to_login_or_none',
        'render_ordinary_page'
    ]

    def dispatch(self, request, slug):
        self.request = request
        self.slug = slug
        if self.using_cache_is_allowed():
            return self.get_page_from_cache()
        else:
            return self.get_page_from_database()

    def get_page_from_cache(self):
        cache_content = get_page_cache(self.request)
        if cache_content is not None:
            response_timestamp = now()
            content, headers, expires_datetime = cache_content
            response = HttpResponse(content)
            response._headers = headers
            # Recalculate the max-age header for this cached response
            max_age = int(
                (expires_datetime - response_timestamp).total_seconds() + 0.5)
            patch_cache_control(response, max_age=max_age)
            return response
        else:
            return self.get_page_from_database()

    def get_page_from_database(self):
        self.page = get_page_from_request(
            self.request,
            use_path=self.slug
        )
        self.current_language = self.get_desired_language()
        for attempt in self.RESPONSE_ATTEMPTS:
            method = getattr(self, attempt)
            response = method()
            if response is not None:
                return response

    #

    def get_404_response_or_none(self):
        if not self.page:
            return _handle_no_page(self.request, self.slug)

    def get_redirect_away_from_root_or_none(self):
        # TODO: If we don't call this method, all tests will still pass.
        # The default django behaviour seems to do
        # roughly what's done here.
        user_languages = get_visible_languages(self.request)
        # Check that the language is in FRONTEND_LANGUAGES:
        if self.current_language not in user_languages:
            if self.root_url_is_requested():
                #redirect to supported language
                available_languages = self.get_available_languages()
                languages = []
                for language in available_languages:
                    languages.append((language, language))
                if languages:
                    # get supported language
                    new_language = get_language_from_request(self.request)
                    if new_language in get_public_languages():
                        return self.get_cms_language_redirection(new_language)
                elif not hasattr(self.request, 'toolbar') or not self.request.toolbar.redirect_url:
                    _handle_no_page(self.request, self.slug)
            else:
                return _handle_no_page(self.request, self.slug)

    def get_redirect_to_fallback_language_or_404_or_none(self):
        available_languages = self.get_available_languages()
        if self.current_language not in available_languages:
            fallback_language = self.get_best_fallback_language()
            if (
                fallback_language
                and self.redirect_to_fallback_language_is_allowed()
            ):
                return self.get_cms_language_redirection(
                    fallback_language
                )
            if (
                not fallback_language
                and not self.toolbar_has_redirect()
            ):
                _handle_no_page(self.request, self.slug)

    def get_redirect_to_proper_slug_or_none(self):
        if not self.slug_is_matching_language():
            url = self.get_page_absolute_url()
            return self.get_cms_redirection(url)

    def get_apphook_response_or_none(self):
        if (
            apphook_pool.get_apphooks()
            and self.following_apphooks_is_allowed()
        ):
            try:
                response = get_app_response_for_page(
                    self.page,
                    self.current_language,
                    self.request
                )
            except Resolver404:
                pass
            else:
                return response

    def get_cms_redirection_or_none(self):
        redirect_url = self.page.get_redirect(
            language=self.current_language
        )
        if redirect_url:
            redirect_url = complete_i18n_url(
                redirect_url,
                self.current_language
            )
            try:
                return self.get_cms_redirection(redirect_url)
            except CircularRedirectionError:
                pass

    def get_redirect_to_login_or_none(self):
        if self.redirect_to_login_is_necessary():
            url = self.request.get_full_path()
            quoted_url = urlquote(url)
            return redirect_to_login(quoted_url, settings.LOGIN_URL)

    def render_ordinary_page(self):
        if hasattr(self.request, 'toolbar'):
            self.request.toolbar.set_object(self.page)
        response = render_page(
            self.request,
            self.page,
            current_language=self.current_language,
            slug=self.slug
        )
        return response

    #

    def get_cms_redirection(self, url):
        if self.message_should_replace_redirect():
            self.request.toolbar.redirect_url = url
        elif not self.url_is_matching_request(url):
            return HttpResponseRedirect(url)
        else:
            raise CircularRedirectionError

    def get_cms_language_redirection(self, language):
        path = self.page.get_absolute_url(
            language=language,
            fallback=True
        )
        try:
            return self.get_cms_redirection(path)
        except CircularRedirectionError:
            return None

    #

    def using_cache_is_allowed(self):
        return get_cms_setting("PAGE_CACHE") and (
            not hasattr(self.request, 'toolbar') or (
                not self.request.toolbar.edit_mode and
                not self.request.toolbar.show_toolbar and
                not self.request.user.is_authenticated()
            )
        )

    def redirect_to_fallback_language_is_allowed(self):
        return (
            get_redirect_on_fallback(self.current_language)
            or self.slug == ""
        )

    def following_apphooks_is_allowed(self):
        return (
            self.page.is_published(self.current_language)
            or not hasattr(self.request, 'toolbar')
            or not self.request.toolbar.edit_mode
        )

    def message_should_replace_redirect(self):
        return (
            hasattr(self.request, 'toolbar')
            and self.request.user.is_staff
            and self.request.toolbar.edit_mode
        )

    def toolbar_has_redirect(self):
        return (
            hasattr(self.request, 'toolbar')
            and self.request.toolbar.redirect_url
        )

    def slug_is_matching_language(self):
        if not self.slug:
            return True
        else:
            url = self.get_page_absolute_url()
            page_slug = self.get_page_slug()
            return (
                self.slug == page_slug
                or self.request.path[:len(url)] == url
            )

    def redirect_to_login_is_necessary(self):
        return (
            self.page.login_required
            and not self.request.user.is_authenticated()
        )

    def url_is_matching_request(self, url):
        protocol = 'https' if self.request.is_secure() else 'http'
        host = self.request.get_host()
        path = self.request.path
        url_variants = [
            '%s://%s%s' % (protocol, host, path),
            '/%s' % path,
            path,
        ]
        return url in url_variants

    def root_url_is_requested(self):
        return not self.slug

    #

    def get_desired_language(self):
        language = get_desired_language(self.request, self.page)
        if not language:
            # TODO: What is the use case for this?
            # This is not present in cms.utils.get_desired_language
            # If we omit this, all tests will still pass:
            language = get_language_code(get_language())
        return language

    def get_available_languages(self):
        user_languages = get_visible_languages(self.request)
        # this will return all languages in draft mode,
        # and published only in live mode:
        page_languages = self.page.get_published_languages()
        intersection = set(user_languages) & set(page_languages)
        return intersection

    def get_best_fallback_language(self):
        available_languages = self.get_available_languages()
        for language in get_fallback_languages(self.current_language):
            if language in available_languages:
                return language

    def get_page_absolute_url(self):
        return self.page.get_absolute_url(
            language=self.current_language
        )

    def get_page_slug(self):
        path = self.page.get_path(language=self.current_language)
        slug = self.page.get_slug(language=self.current_language)
        return path or slug
