from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from cms import settings
from cms.models import Page
from cms.utils import auto_render, get_template_from_request, get_language_from_request
from django.db.models.query_utils import Q
from cms.appresolver import applications_page_check
from django.contrib.sites.models import Site

def _get_current_page(path, lang):
    """Helper for getting current page from path depending on language
    
    returns: Page or None
    """
    try:
        return Page.objects.published().filter( 
            Q(title_set__path=path[:-1], title_set__language=lang)).distinct().select_related()[0]
    except IndexError:
        return None

def details(request, page_id=None, slug=None, template_name=settings.CMS_TEMPLATES[0][0], no404=False):
    lang = get_language_from_request(request)
    site = Site.objects.get_current()
    pages = Page.objects.published().filter(parent__isnull=True).order_by("tree_id")
    current_page, response = None, None
    if pages:
        if page_id:
            current_page = get_object_or_404(Page.objects.published(site), pk=page_id)
        elif slug != None:
            if slug == "":
                current_page = pages[0]
            else:
                path = request.path.replace(reverse('pages-root'), '', 1)
                current_page = _get_current_page(path, lang)
                if settings.CMS_APPLICATIONS_URLS:
                    # check if it should'nt point to some application, if yes,
                    # change current page if required
                    current_page = applications_page_check(request, current_page, path)
                
                if not current_page:
                    raise Http404('CMS Page not found')
        else:
            current_page = applications_page_check(request)
            #current_page = None
        template_name = get_template_from_request(request, current_page)
    elif not no404:
        raise Http404("no page found for site %s" % unicode(site.name))
    if current_page:  
        has_page_permissions = current_page.has_page_permission(request)
        request._current_page_cache = current_page
    else:
        has_page_permissions = False
        
    return template_name, locals()
details = auto_render(details)