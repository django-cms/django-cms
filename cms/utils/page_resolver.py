# -*- coding: utf-8 -*-
import urllib
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ungettext_lazy

from cms.exceptions import NoHomeFound
from cms.models.pagemodel import Page
from cms.utils.urlutils import any_path_re

ADMIN_PAGE_RE_PATTERN = ur'cms/page/(\d+)'
ADMIN_PAGE_RE = re.compile(ADMIN_PAGE_RE_PATTERN)


def use_draft(request):
    """
    Decision function to determine if the drafts or public pages should be used
    Public models are used unless looking at preview or edit versions of the page.
    """
    preview_draft = 'preview' in request.GET and 'draft' in request.GET
    edit_mode = 'edit' in request.GET

    return preview_draft or edit_mode


def get_page_queryset(request=None):
    if request and use_draft(request):
        return Page.objects.drafts()

    return Page.objects.public()


def get_page_queryset_from_path(path, preview=False, draft=False, site=None):
    """ Returns a queryset of pages corresponding to the path given
    In may returns None or a single page is no page is present or root path is given
    """
    if 'django.contrib.admin' in settings.INSTALLED_APPS:
        admin_base = reverse('admin:index')
    else:
        admin_base = None

    # Check if this is called from an admin request
    if admin_base and path.startswith(admin_base):
        # if so, get the page ID to request it directly
        match = ADMIN_PAGE_RE.search(path)
        if not match:
            page = None
        else:
            try:
                page = Page.objects.get(pk=match.group(1))
            except Page.DoesNotExist:
                page = None
        return page

    if not site:
        site = Site.objects.get_current()

    # PageQuerySet.published filter on page site.
    # We have to explicitly filter on site only in preview mode
    if draft:
        pages = Page.objects.drafts().filter(site=site)
    elif preview:
        pages = Page.objects.public().filter(site=site)
    else:
        pages = Page.objects.public().published(site)

    # Check if there are any pages
    if not pages.all_root().exists():
        return None

    # get the home page (needed to get the page)
    try:
        home = pages.get_home(site=site)
    except NoHomeFound:
        home = None
    # if there is no path (slashes stripped) and we found a home, this is the
    # home page.
    if not path and home:
        page = home
        return page

    # title_set__path=path should be clear, get the pages where the path of the
    # title object is equal to our path.
    return pages.filter(title_set__path=path).distinct()


def get_page_from_path(path, preview=False, draft=False):
    """ Resolves a url path to a single page object.
    Raises exceptions is page does not exist or multiple pages are found
    """
    page_qs = get_page_queryset_from_path(path, preview, draft)
    if page_qs is not None:
        if isinstance(page_qs, Page):
            return page_qs
        try:
            page = page_qs.get()
        except Page.DoesNotExist:
            return None
        return page
    else:
        return None


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

    # The following is used by cms.middleware.page.CurrentPageMiddleware
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache

    draft = use_draft(request)
    preview = 'preview' in request.GET
    # If non-staff user, any request for preview/edit results in a "not found"
    # This is to avoid confusing the toolbar logic into thinking it has an
    # editable version
    if draft and not request.user.is_authenticated():
        return None

    # If use_path is given, someone already did the path cleaning
    if use_path is not None:
        path = use_path
    else:
        path = request.path
        pages_root = urllib.unquote(reverse("pages-root"))
        # otherwise strip off the non-cms part of the URL
        if 'django.contrib.admin' in settings.INSTALLED_APPS:
            admin_base = reverse('admin:index')
        else:
            admin_base = None
        if path.startswith(pages_root) and (not admin_base or not path.startswith(admin_base)):
            path = path[len(pages_root):]
        # and strip any final slash
        if path.endswith("/"):
            path = path[:-1]

    page = get_page_from_path(path, preview, draft)
    if draft and page and not page.has_change_permission(request):
        return None

    request._current_page_cache = page
    return page


def is_valid_url(url, instance, create_links=True, site=None):
    """ Checks for conflicting urls
    """
    page_root = urllib.unquote(reverse("pages-root"))
    if url and url != page_root:
        # Url sanity check via regexp
        if not any_path_re.match(url):
            raise ValidationError(_('Invalid URL, use /my/url format.'))
        # We only check page FK to site object to allow is_valid_url check on
        # incomplete Page instances
        if not site and instance.site_id:
            site = instance.site
        # Retrieve complete queryset of pages with corresponding URL
        # This uses the same resolving function as ``get_page_from_path``
        if url.startswith(page_root):
            url = url[len(page_root):]
        page_qs = get_page_queryset_from_path(url.strip('/'), site=site)
        url_clashes = []
        # If queryset has pages checks for conflicting urls
        if page_qs is not None:
            # If single page is returned create a list for interface compat
            if isinstance(page_qs, Page):
                page_qs = [page_qs]
            for page in page_qs:
                # Every page in the queryset except the current one is a conflicting page
                # We have to exclude both copies of the page
                if page and page.publisher_public.pk != instance.pk:
                    if create_links:
                        # Format return message with page url
                        url_clashes.append('<a href="%(page_url)s%(pk)s" target="_blank">%(page_title)s</a>' % {
                            'page_url': reverse('admin:cms_page_changelist'), 'pk': page.pk,
                            'page_title': force_unicode(page),
                        })
                    else:
                        # Just return the page name
                        url_clashes.append("'%s'" % page)
            if url_clashes:
                # If clashing pages exist raise the exception
                raise ValidationError(mark_safe(
                    ungettext_lazy('Page %(pages)s has the same url \'%(url)s\' as current page "%(instance)s".',
                                   'Pages %(pages)s have the same url \'%(url)s\' as current page "%(instance)s".',
                                    len(url_clashes)) %
                    {'pages': ', '.join(url_clashes), 'url': url, 'instance': instance}))
    return True
