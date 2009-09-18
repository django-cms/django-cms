from cms import settings
from cms.appresolver import applications_page_check
from cms.utils import auto_render, get_template_from_request, \
    get_language_from_request
from cms.utils.moderator import get_page_queryset
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.http import urlquote
from django.conf import settings as django_settings

def get_current_page(path, lang, queryset, home_slug, home_tree_id):
    """Helper for getting current page from path depending on language
    
    returns: (Page, None) or (None, path_to_alternative language)
    """
    try:
        if home_slug:
            queryset = queryset.exclude(Q(title_set__path=home_slug)&Q(tree_id=home_tree_id))
            home_slug += "/"
            title_q = Q(title_set__path=path)|(Q(title_set__path=home_slug + path)&Q(tree_id=home_tree_id))
            
        else:
            title_q = Q(title_set__slug=path)
        if settings.CMS_FLAT_URLS:
            return queryset.filter(title_q & Q(title_set__language=lang)).distinct().select_related()[0], None
        else:
            page = queryset.filter(title_q).distinct().select_related()[0]
            if page:
                langs = page.get_languages() 
                if lang in langs:
                    return page, None
                else:
                    path = None
                    for alt_lang in settings.LANGUAGES:
                        if alt_lang[0] in langs:
                            path = '/%s%s' % (alt_lang[0], page.get_absolute_url(language=lang, fallback=True))
                    return None, path
    except IndexError:
        return None, None

def details(request, page_id=None, slug=None, template_name=settings.CMS_TEMPLATES[0][0], no404=False):
    # get the right model
    page_queryset = get_page_queryset(request)
    
    lang = get_language_from_request(request)
    site = Site.objects.get_current()
    if 'preview' in request.GET.keys():
        pages = page_queryset.all()
    else:
        pages = page_queryset.published()
    
    root_pages = pages.all_root().order_by("tree_id")
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
                if root_pages:
                    home_tree_id = root_pages[0].tree_id
                    home_slug = root_pages[0].get_slug(language=lang)
                else:
                    home_slug = ""
                    home_tree_id = None
                current_page, alternative = get_current_page(path, lang, pages, home_slug, home_tree_id)
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
        has_change_permissions = current_page.has_change_permission(request)
        request._current_page_cache = current_page
        if current_page.get_redirect(language=lang):
            return HttpResponseRedirect(current_page.get_redirect(language=lang))
        if current_page.login_required and not request.user.is_authenticated():
            if 'cms.middleware.multilingual.MultilingualURLMiddleware' in django_settings.MIDDLEWARE_CLASSES:
                path = urlquote("/%s%s" % (request.LANGUAGE_CODE, request.get_full_path()))
            else:
                path = urlquote(request.get_full_path())
            tup = django_settings.LOGIN_URL , "next", path
            return HttpResponseRedirect('%s?%s=%s' % tup)
    else:
        has_change_permissions = False
    return template_name, locals()
details = auto_render(details)
