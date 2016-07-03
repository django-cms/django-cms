# -*- coding: utf-8 -*-
import re

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.six.moves.urllib.parse import unquote
from django.utils.translation import ugettext_lazy as _, ungettext_lazy

from cms.models.pagemodel import Page
from cms.utils.compat.dj import is_installed
from cms.utils.moderator import use_draft
from cms.utils.urlutils import any_path_re, admin_reverse
from cms.utils.page_permissions import user_can_change_page


ADMIN_PAGE_RE_PATTERN = r'cms/page/(\d+)'
ADMIN_PAGE_RE = re.compile(ADMIN_PAGE_RE_PATTERN)


def get_page_queryset(request=None):
    if request and use_draft(request):
        return Page.objects.drafts()

    return Page.objects.public()


def get_page_queryset_from_path(path, preview=False, draft=False, site=None):
    """ Returns a queryset of pages corresponding to the path given
    """
    if is_installed('django.contrib.admin'):
        admin_base = admin_reverse('index')

        # Check if this is called from an admin request
        if path.startswith(admin_base):
            # if so, get the page ID to request it directly
            match = ADMIN_PAGE_RE.search(path)
            if match:
                return Page.objects.filter(pk=match.group(1))
            else:
                return Page.objects.none()

    if not site:
        site = Site.objects.get_current()

    # PageQuerySet.published filter on page site.
    # We have to explicitly filter on site only in preview mode
    if draft:
        pages = Page.objects.drafts().filter(site=site)
    elif preview:
        pages = Page.objects.public().filter(site=site)
    else:
        pages = Page.objects.public().published(site=site)

    if not path:
        # if there is no path (slashes stripped) and we found a home, this is the
        # home page.
        # PageQuerySet.published() introduces a join to title_set which can return
        # multiple rows. Get only the first match.
        return pages.filter(is_home=True, site=site)[:1]

    # title_set__path=path should be clear, get the pages where the path of the
    # title object is equal to our path.
    return pages.filter(title_set__path=path).distinct()


def get_page_from_path(path, preview=False, draft=False):
    """ Resolves a url path to a single page object.
    Returns None if page does not exist
    """
    try:
        return get_page_queryset_from_path(path, preview, draft).get()
    except Page.DoesNotExist:
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
    # If use_path is given, someone already did the path cleaning
    if use_path is not None:
        path = use_path
    else:
        path = request.path_info
        pages_root = unquote(reverse("pages-root"))
        # otherwise strip off the non-cms part of the URL
        if is_installed('django.contrib.admin'):
            admin_base = admin_reverse('index')
        else:
            admin_base = None
        if path.startswith(pages_root) and (not admin_base or not path.startswith(admin_base)):
            path = path[len(pages_root):]
            # and strip any final slash
        if path.endswith("/"):
            path = path[:-1]

    page = get_page_from_path(path, preview, draft)

    if draft and page and not user_can_change_page(request.user, page):
        page = get_page_from_path(path, preview, draft=False)

    # For public pages we check if any parent is hidden due to published dates
    # In this case the selected page is not reachable
    if page and not draft:
        ancestors = page.get_ancestors().filter(
            Q(publication_date__gt=timezone.now()) | Q(publication_end_date__lt=timezone.now()),
        )
        if ancestors.exists():
            page = None

    request._current_page_cache = page
    return page


def is_valid_url(url, instance, create_links=True, site=None):
    """ Checks for conflicting urls
    """
    page_root = unquote(reverse("pages-root"))
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
        page_qs = get_page_queryset_from_path(url.strip('/'), site=site, draft=instance.publisher_is_draft)
        url_clashes = []
        # If queryset has pages checks for conflicting urls
        for page in page_qs:
            # Every page in the queryset except the current one is a conflicting page
            # We have to exclude both copies of the page
            if page and page.publisher_public_id != instance.pk and page.pk != instance.pk:
                if create_links:
                    # Format return message with page url
                    url_clashes.append('<a href="%(page_url)s%(pk)s" target="_blank">%(page_title)s</a>' % {
                        'page_url': admin_reverse('cms_page_changelist'), 'pk': page.pk,
                        'page_title': force_text(page),
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
