# -*- coding: utf-8 -*-
from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_urls
from cms.utils import get_template_from_request, get_language_from_request
from cms.utils.i18n import get_fallback_languages
from cms.utils.page_resolver import get_page_from_request
from django.conf import settings
from django.conf.urls.defaults import patterns
from django.core.urlresolvers import resolve, Resolver404

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
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
    
    # Check that the current page is available in the desired (current) language
    available_languages = page.get_languages()
    
    # We resolve an alternate language for the page if it's not available.
    # Since the "old" details view had an exception for the root page, it is
    # ported here. So no resolution if the slug is ''.
    if (current_language not in available_languages):
        if settings.CMS_LANGUAGE_FALLBACK:
            # If we didn't find the required page in the requested (current) 
            # language, let's try to find a suitable fallback in the list of 
            # fallback languages (CMS_LANGUAGE_CONF)
            for alt_lang in get_fallback_languages(current_language):
                if alt_lang in available_languages:
                    alt_url = page.get_absolute_url(language=alt_lang, fallback=True)
                    path = '/%s%s' % (alt_lang, alt_url)
                    # In the case where the page is not available in the
                    # preferred language, *redirect* to the fallback page. This
                    # is a design decision (instead of rendering in place)).
                    return HttpResponseRedirect(path)
        # There is a page object we can't find a proper language to render it 
        _handle_no_page(request, slug)

    if apphook_pool.get_apphooks():
        # There are apphooks in the pool. Let's see if there is one for the
        # current page
        # since we always have a page at this point, applications_page_check is
        # pointless
        # page = applications_page_check(request, page, slug)
        # Check for apphooks! This time for real!
        app_urls = page.get_application_urls(current_language, False)
        if app_urls:
            app = apphook_pool.get_apphook(app_urls)
            pattern_list = []
            for urlpatterns in get_app_urls(app.urls):
                pattern_list += urlpatterns
            urlpatterns = patterns('', *pattern_list)
            try:
                view, args, kwargs = resolve('/', tuple(urlpatterns))
                return view(request, *args, **kwargs)
            except Resolver404:
                pass

    # Check if the page has a redirect url defined for this language. 
    redirect_url = page.get_redirect(language=current_language)
    if redirect_url:
        if (settings.i18n_installed and redirect_url[0] == "/"
            and not redirect_url.startswith('/%s/' % current_language)):
            # add language prefix to url
            redirect_url = "/%s/%s" % (current_language, redirect_url.lstrip("/"))
        # prevent redirect to self
        own_urls = [
            'http%s://%s%s' % ('s' if request.is_secure() else '', request.get_host(), request.path),
            '/%s%s' % (current_language, request.path),
            request.path,
        ]
        if redirect_url not in own_urls:
            return HttpResponseRedirect(redirect_url)
    
    # permission checks
    if page.login_required and not request.user.is_authenticated():
        if settings.i18n_installed:
            path = urlquote("/%s%s" % (request.LANGUAGE_CODE, request.get_full_path()))
        else:
            path = urlquote(request.get_full_path())
        tup = settings.LOGIN_URL , "next", path
        return HttpResponseRedirect('%s?%s=%s' % tup)
    
    template_name = get_template_from_request(request, page, no_current_page=True)
    # fill the context 
    context['lang'] = current_language
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    context['has_view_permissions'] = page.has_view_permission(request)
    
    if not context['has_view_permissions']:
        return _handle_no_page(request, slug)
    
    return render_to_response(template_name, context)
