from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import SITE_CACHE
from django.core.urlresolvers import reverse
from cms import settings
from cms.models import Page, Title
from cms.utils import auto_render, get_template_from_request, get_language_from_request
from django.db.models.query_utils import Q


def details(request, page_id=None, slug=None, template_name=settings.DEFAULT_CMS_TEMPLATE, no404=False):
    lang = get_language_from_request(request)
    site = request.site
    pages = Page.objects.root(site).order_by("tree_id")
    if pages:
        if page_id:
            current_page = get_object_or_404(Page.objects.published(site), pk=page_id)
        elif slug != None:
            if slug == "":
                current_page = pages[0]
            else:
                path = request.path.replace(reverse('pages-root'), '', 1)
                current_page = get_object_or_404(Page.objects.published(site), Q(status=Page.PUBLISHED, has_url_overwrite=True, url_overwrite=path)|Q(title_set__path=path[:-1]))
        else:
            current_page = None
        template_name = get_template_from_request(request, current_page)
    else:
        if no404:# used for placeholder finder
            current_page = None
        else:
            raise Http404, "no page found for this site"  
    if current_page:  
        has_page_permissions = current_page.has_page_permission(request)
    else:
        has_page_permissions = False
    if current_page:
        request._current_page_cache = current_page
    return template_name, locals()
details = auto_render(details)
