# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import resolve, Resolver404, reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.cache import patch_cache_control
from django.utils.translation import get_language
from django.utils.http import urlquote
from django.utils.timezone import now
from django.views.generic import View

from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_urls
from cms.cache.page import get_page_cache
from cms.page_rendering import _handle_no_page, render_page
from cms.utils import get_language_from_request, get_cms_setting, get_desired_language
from cms.utils.i18n import (get_fallback_languages, force_language, get_public_languages,
                            get_redirect_on_fallback, get_language_list, complete_i18n_url,
                            get_language_code)
from cms.utils.page_resolver import get_page_from_request


class NoHttpResponseReturned(Exception):
    pass


class CircularRedirectionError(Exception):
    pass


def details(request, slug):
    view = PageView.as_view()
    return view(request, slug)


class PageView(View):
    """
    The main view of the Django-CMS! Takes a request and a slug, renders the
    page.
    """
    RESPONSE_ATTEMPTS = ['render_404', 'ugly_language_redirect_code',
                         'redirect_to_correct_slug', 'follow_apphook',
                         'follow_page_redirect', 'redirect_to_login']

    def dispatch(self, request, slug):
        self.request = request
        self.slug = slug
        if self.using_cache_is_fine():
            return self.page_from_cache()
        else:
            return self.page_from_database()

    def page_from_cache(self):
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
            return self.page_from_database()

    def page_from_database(self):
        # Get a Page model object from the self.request
        self.page = get_page_from_request(self.request, use_path=self.slug)
        self.current_language = self.get_desired_language()
        for response_name in self.RESPONSE_ATTEMPTS:
            try:
                response = getattr(self, response_name)
                return response()
            except NoHttpResponseReturned:
                continue
        return self.render_ordinary_page()

    def render_404(self):
        if not self.page:
            return _handle_no_page(self.request, self.slug)
        else:
            raise NoHttpResponseReturned

    def redirect_to_correct_slug(self):
        page_path = self.get_page_path()
        page_slug = self.get_page_slug()
        if self.slug and self.slug != page_slug and self.request.path[:len(page_path)] != page_path:
            # The current language does not match it's slug.
            #  Redirect to the current language.
            return self.cms_redirection(page_path)
        raise NoHttpResponseReturned

    def follow_apphook(self):
        if apphook_pool.get_apphooks():
            # There are apphooks in the pool. Let's see if there is one for the
            # current page
            # since we always have a page at this point, applications_page_check is
            # pointless
            # page = applications_page_check(request, page, slug)
            # Check for apphooks! This time for real!
            app_urls = self.page.get_application_urls(self.current_language, False)
            skip_app = False
            if (not self.page.is_published(self.current_language) and hasattr(self.request, 'toolbar')
                    and self.request.toolbar.edit_mode):
                skip_app = True
            if app_urls and not skip_app:
                app = apphook_pool.get_apphook(app_urls)
                pattern_list = []
                if app:
                    for urlpatterns in get_app_urls(app.get_urls(self.page, self.current_language)):
                        pattern_list += urlpatterns
                    try:
                        view, args, kwargs = resolve('/', tuple(pattern_list))
                        return view(self.request, *args, **kwargs)
                    except Resolver404:
                        pass
        raise NoHttpResponseReturned

    def follow_page_redirect(self):
        # Check if the page has a redirect url defined for this language.
        redirect_url = self.page.get_redirect(language=self.current_language)
        if redirect_url:
            redirect_url = complete_i18n_url(redirect_url, self.current_language)
            try:
                return self.cms_redirection(redirect_url)
            except CircularRedirectionError:
                pass
        raise NoHttpResponseReturned

    def redirect_to_login(self):
        # permission checks
        if self.page.login_required and not self.request.user.is_authenticated():
            return redirect_to_login(urlquote(self.request.get_full_path()), settings.LOGIN_URL)
        else:
            raise NoHttpResponseReturned

    def render_ordinary_page(self):
        if hasattr(self.request, 'toolbar'):
            self.request.toolbar.set_object(self.page)
        response = render_page(self.request, self.page, current_language=self.current_language, slug=self.slug)
        return response

    def cms_redirection(self, url):
        if self.redirects_should_wait():
            self.request.toolbar.redirect_url = url
            raise NoHttpResponseReturned
        elif not self.url_matches_request(url):
            return HttpResponseRedirect(url)
        else:
            raise CircularRedirectionError

    def using_cache_is_fine(self):
        return get_cms_setting("PAGE_CACHE") and (
            not hasattr(self.request, 'toolbar') or (
                not self.request.toolbar.edit_mode and
                not self.request.toolbar.show_toolbar and
                not self.request.user.is_authenticated()
            )
        )

    def redirects_should_wait(self):
        """
        Determine who should see a message about the redirect
        instead of being redirected.
        """
        return (
            hasattr(self.request, 'toolbar')
            and self.request.user.is_staff
            and self.request.toolbar.edit_mode
        )

    def url_matches_request(self, url):
        url_variants = [
            'http%s://%s%s' % ('s' if self.request.is_secure() else '', self.request.get_host(), self.request.path),
            '/%s' % self.request.path,
            self.request.path,
        ]
        return url in url_variants

    def get_desired_language(self):
        language = get_desired_language(self.request, self.page)
        if not language:
            # TODO: What is the use case for this?
            # This is not present in cms.utils.get_desired_language.
            language = get_language_code(get_language())
        return language

    def get_page_path(self):
        return self.page.get_absolute_url(language=self.current_language)

    def get_page_slug(self):
        return self.page.get_path(language=self.current_language) or self.page.get_slug(language=self.current_language)

    def ugly_language_redirect_code(self):
        # Check that the current page is available in the desired (current) language
        available_languages = []
        # this will return all languages in draft mode, and published only in live mode
        page_languages = list(self.page.get_published_languages())
        if hasattr(self.request, 'user') and self.request.user.is_staff:
            user_languages = get_language_list()
        else:
            user_languages = get_public_languages()
        for frontend_lang in user_languages:
            if frontend_lang in page_languages:
                available_languages.append(frontend_lang)
        # Check that the language is in FRONTEND_LANGUAGES:
        if self.current_language not in user_languages:
            #are we on root?
            if not self.slug:
                #redirect to supported language
                languages = []
                for language in available_languages:
                    languages.append((language, language))
                if languages:
                    # get supported language
                    new_language = get_language_from_request(self.request)
                    if new_language in get_public_languages():
                        with force_language(new_language):
                            pages_root = reverse('pages-root')
                            try:
                                return self.cms_redirection(pages_root)
                            except CircularRedirectionError:
                                pass
                elif not hasattr(self.request, 'toolbar') or not self.request.toolbar.redirect_url:
                    _handle_no_page(self.request, self.slug)
            else:
                return _handle_no_page(self.request, self.slug)
        if self.current_language not in available_languages:
            # If we didn't find the required page in the requested (current)
            # language, let's try to find a fallback
            found = False
            for alt_lang in get_fallback_languages(self.current_language):
                if alt_lang in available_languages:
                    if get_redirect_on_fallback(self.current_language) or self.slug == "":
                        with force_language(alt_lang):
                            path = self.page.get_absolute_url(language=alt_lang, fallback=True)
                            # In the case where the page is not available in the
                        # preferred language, *redirect* to the fallback page. This
                        # is a design decision (instead of rendering in place)).
                        try:
                            return self.cms_redirection(path)
                        except CircularRedirectionError:
                            pass
                    else:
                        found = True
            if not found and (not hasattr(self.request, 'toolbar') or not self.request.toolbar.redirect_url):
                # There is a page object we can't find a proper language to render it
                _handle_no_page(self.request, self.slug)
        raise NoHttpResponseReturned
