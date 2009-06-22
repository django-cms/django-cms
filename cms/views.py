from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from cms import settings
from cms.models import Page
from cms.utils import auto_render, get_template_from_request, get_language_from_request
from django.db.models.query_utils import Q
from cms.appresolver import applications_page_check
from django.contrib.sites.models import Site

def _get_current_page(path, lang, queryset):
    """Helper for getting current page from path depending on language
    
    returns: (Page, None) or (None, path_to_alternative language)
    """
    try:
        if settings.CMS_FLAT_URLS:
            return queryset.filter(Q(title_set__slug=path,
                                                     title_set__language=lang)).distinct().select_related()[0]
        else:
            page = queryset.filter(title_set__path=path).distinct().select_related()[0]
            if page:
                langs = page.get_languages() 
                if lang in langs:
                    return page, None
                else:
                    path = None
                    for alt_lang in settings.LANGUAGES:
                        if alt_lang[0] in langs:
                            path = '/%s%s' % (alt_lang[0][:2], page.get_absolute_url(language=lang, fallback=True))
                    return None, path
    except IndexError:
        return None, None

def details(request, page_id=None, slug=None, template_name=settings.CMS_TEMPLATES[0][0], no404=False):
    lang = get_language_from_request(request)
    site = Site.objects.get_current()
    if 'preview' in request.GET.keys():
        pages = Page.objects.all()
    else:
        pages = Page.objects.published()
    root_pages = pages.filter(parent__isnull=True).order_by("tree_id")
    current_page, response = None, None
    if root_pages:
        if page_id:
            current_page = get_object_or_404(pages, pk=page_id)
        elif slug != None:
            if slug == "":
                current_page = root_pages[0]
            else:
                if slug.startswith(reverse('pages-root')):
                    path = slug.replace(reverse('pages-root'), '', 1)
                else:
                    path = slug
                current_page, alternative = _get_current_page(path, lang, pages)
                if settings.CMS_APPLICATIONS_URLS:
                    # check if it should'nt point to some application, if yes,
                    # change current page if required
                    current_page = applications_page_check(request, current_page, path)
                if not current_page:
                    if alternative and settings.CMS_LANGUAGE_FALLBACK:
                        return HttpResponseRedirect(alternative)
                    if no404:# used for placeholder finder
                        current_page = None
                    else:
                        raise Http404('CMS: Page not found for "%s"' % slug)
        else:
            current_page = applications_page_check(request)
            #current_page = None
        template_name = get_template_from_request(request, current_page)
    elif not no404:
        raise Http404("CMS: No page found for site %s" % unicode(site.name))
    if current_page:  
        has_page_permissions = current_page.has_page_permission(request)
        request._current_page_cache = current_page
        if current_page.get_redirect(language=lang):
            return HttpResponseRedirect(current_page.get_redirect(language=lang))
    else:
        has_page_permissions = False
    return template_name, locals()
details = auto_render(details)
