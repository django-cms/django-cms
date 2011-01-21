# -*- coding: utf-8 -*-
from cms.exceptions import NoHomeFound
from cms.models.pagemodel import Page
from cms.utils.moderator import get_page_queryset
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
import urllib


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
    if 'django.contrib.admin' in settings.INSTALLED_APPS:
        admin_base = reverse('admin:index')
    else:
        admin_base = None
    
    pages_root = urllib.unquote(reverse("pages-root"))
    
    # The following is used by cms.middleware.page.CurrentPageMiddleware
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache
    
    # Get a basic queryset for Page objects, depending on if we use the 
    # MODERATOR or not.
    page_queryset = get_page_queryset(request)
    site = Site.objects.get_current()
    
    # Check if this is called from an admin request
    if admin_base and request.path.startswith(admin_base):
        # if so, get the page ID to query the page
        page_id = [bit for bit in request.path.split('/') if bit][-1]
        if not page_id or not page_id.isdigit():
            page = None
        else:
            try:
                page = Page.objects.get(pk=page_id)
            except Page.DoesNotExist:
                return None
        request._current_page_cache = page
        return page
    
    # TODO: Isn't there a permission check needed here?
    if 'preview' in request.GET:
        pages = page_queryset.filter(site=site)
    else:
        pages = page_queryset.published().filter(site=site)
    
    # If use_path is given, someone already did the path cleaning
    if use_path:
        path = use_path
    else:
        # otherwise strip of the non-cms part of the URL 
        path = request.path[len(pages_root):-1]
        
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
        request._current_page_cache = page
        return page
    
    # title_set__path=path should be clear, get the pages where the path of the
    # title object is equal to our path.
    if settings.CMS_FLAT_URLS:
        q = Q(title_set__slug=path)
    else:
        q = Q(title_set__path=path)
        if home:
            # if we have a home, also search for all paths prefixed with the
            # home slug that are on the same tree as home, since home isn't ussually
            # called with it's slug, thus it's children don't have the home bit in
            # the request either, thus we need to re-add it.
            q2 = Q()
            q2 = Q(title_set__path='%s/%s' % (home.get_slug(), path))
            q2 &= Q(tree_id=home.tree_id)
            q |= q2
        
    if settings.CMS_DBGETTEXT and settings.CMS_DBGETTEXT_SLUGS: # pragma: no cover
        #=======================================================================
        # WARNING: CMS_DBGETTEXT WILL BE DEPRECATED IN 2.2!
        #=======================================================================
        from django.utils.translation import ugettext
        from cms.models import Title
        for t in Title.objects.all():
            tpath = '/'.join([ugettext(x) for x in t.path.split('/')])
            if path == tpath:
                q = Q(title_set__path=t.path)
                break
    try:
        page = pages.filter(q).distinct().get()
    except Page.DoesNotExist:
        return None
    request._current_page_cache = page
    return page