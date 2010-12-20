from cms.apphook_pool import apphook_pool
from cms.appresolver import applications_page_check
from cms.utils import get_template_from_request, get_language_from_request
from cms.utils.i18n import get_fallback_languages
from cms.utils.page_resolver import get_page_from_request
from django.conf import settings, settings as django_settings
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.http import urlquote


def _handle_no_page(request, slug):
    if not slug and settings.DEBUG:
        CMS_MEDIA_URL = settings.CMS_MEDIA_URL
        return "cms/new.html", locals()
    raise Http404('CMS: Page not found for "%s"' % slug)

def details(request, slug):
    # get the right model
    context = RequestContext(request)
    # Get a Page model object from the request
    page = get_page_from_request(request, use_path=slug)
    if not page:
        _handle_no_page(request, slug)
    
    current_language = get_language_from_request(request)
    
    # Check that the current page is available in the desired (current) language
    available_languages = page.get_languages()
    # We resolve an alternate language for the page if it's not available.
    # Since the "old" details view had an exception for the root page, it is
    # ported here. So no resolution if the slug is ''.
    if (current_language not in available_languages) and (slug != ''):
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
        page = applications_page_check(request, page, slug)
    redirect_url = page.get_redirect(language=current_language)
    if redirect_url:
        if settings.i18n_installed and redirect_url[0] == "/":
            redirect_url = "/%s/%s" % (current_language, redirect_url.lstrip("/"))
        # add language prefix to url
        return HttpResponseRedirect(redirect_url)
    
    if page.login_required and not request.user.is_authenticated():
        if settings.i18n_installed:
            path = urlquote("/%s%s" % (request.LANGUAGE_CODE, request.get_full_path()))
        else:
            path = urlquote(request.get_full_path())
        tup = django_settings.LOGIN_URL , "next", path
        return HttpResponseRedirect('%s?%s=%s' % tup)
    context['lang'] = current_language
    context['current_page'] = page
    template_name = get_template_from_request(request, page, no_current_page=True)
    context['has_change_permissions'] = page.has_change_permission(request)
    return render_to_response(template_name, context)
