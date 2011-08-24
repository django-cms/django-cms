# -*- coding: utf-8 -*-
from cms.exceptions import NoHomeFound
from cms.models.pagemodel import Page

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
import urllib
import re

ADMIN_PAGE_RE_PATTERN = ur'cms/page/(\d+)'
ADMIN_PAGE_RE = re.compile(ADMIN_PAGE_RE_PATTERN)


def get_page_from_path(path, preview=False):
    if 'django.contrib.admin' in settings.INSTALLED_APPS:
        admin_base = reverse('admin:index').lstrip('/')
    else:
        admin_base = None
    
    site = Site.objects.get_current()
    # Check if this is called from an admin request
    if admin_base and path.startswith(admin_base):
        # if so, get the page ID to query the page
        match = ADMIN_PAGE_RE.search(path)
        if not match:
            page = None
        else:
            try:
                page = Page.objects.get(pk=match.group(1))
            except Page.DoesNotExist:
                page = None
        return page
    
    if not settings.CMS_MODERATOR or preview:
        # We do not use moderator
        pages = Page.objects.drafts()
    else:
        pages = Page.objects.public()
    
    if not preview:
        pages = pages.published()

    pages = pages.filter(site=site)
    
    # Check if there are any pages
    if not pages.all_root():
        return None
    
    # get the home page (needed to get the page)
    try:
        home = pages.get_home()
    except NoHomeFound:
        home = None
    # if there is no path (slashes stripped) and we found a home, this is the
    # home page.
    if not path and home:
        page = home
        return page
    
    # title_set__path=path should be clear, get the pages where the path of the
    # title object is equal to our path.
    if settings.CMS_FLAT_URLS:
        q = Q(title_set__slug=path)
    else:
        q = Q(title_set__path=path)
    try:
        page = pages.filter(q).distinct().get()
    except Page.DoesNotExist:
        return None
        
    return page
    

def get_page_from_request(request, use_path=None):
    """
    Gets the current page from a request object.
    
    URLs can be of the following form (this should help understand the code):
    http://server.whatever.com/<some_path>/"pages-root"/some/page/slug
    
    <some_path>: This can be anything, and should be stripped when resolving
        pages names. This means the CMS is not installed at the root of the 
        server's URLs.
    "pages-root" This is the root of Django urls for the CMS. It is, in essence
        an empty page slug (slug == '')
        
    The page slug can then be resolved to a Page model object
    """
    pages_root = urllib.unquote(reverse("pages-root"))
    
    # The following is used by cms.middleware.page.CurrentPageMiddleware
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache

    # TODO: Isn't there a permission check needed here?
    preview = 'preview' in request.GET and request.user.is_staff

    # If use_path is given, someone already did the path cleaning
    if use_path:
        path = use_path
    else:
        # otherwise strip of the non-cms part of the URL 
        path = request.path[len(pages_root):-1]
    
    page = get_page_from_path(path, preview)
        
    request._current_page_cache = page
    return page
