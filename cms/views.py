from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import SITE_CACHE

from cms import settings
from cms.models import Page, Title
from cms.utils import auto_render, get_template_from_request, get_language_from_request


def details(request, page_id=None, slug=None, template_name=settings.DEFAULT_CMS_TEMPLATE):
    lang = get_language_from_request(request)
    site = request.site
    pages = Page.objects.root(site).order_by("tree_id")
    if pages:
        if page_id:
            current_page = get_object_or_404(Page.objects.published(site), pk=page_id)
        elif slug:
            slug_titles = Title.objects.get_page_slug(slug, site)
            if len(slug_titles) == 1:
                slug_title = slug_titles[0]
                if slug_title and slug_title.page.calculated_status == Page.PUBLISHED:
                    current_page = slug_title.page
                else:
                    raise Http404
            elif len(slug_titles) > 1:
                print slug
                print slug_titles
                raise "more than one" #TODO: implement
            else:
                raise Http404
        else:
            current_page = pages[0]
        template_name = get_template_from_request(request, current_page)
    else:
        raise Http404, "no page found for this site"
        #current_page = None
        
        
    has_page_permissions = current_page.has_page_permission(request)
    return template_name, locals()
details = auto_render(details)
