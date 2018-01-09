# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_text

from cms.constants import PAGE_USERNAME_MAX_LENGTH
from cms.utils import get_current_site
from cms.utils.conf import get_cms_setting
from cms.utils.moderator import use_draft


SUFFIX_REGEX = re.compile(r'^(.*)-(\d+)$')


def _page_is_published(page):
    the_now = timezone.now()
    reachable = True

    if page.publication_date:
        reachable = page.publication_date <= the_now

    if page.publication_end_date:
        reachable = reachable and page.publication_end_date > the_now
    return reachable


def get_page_template_from_request(request):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    templates = get_cms_setting('TEMPLATES')
    template_names = frozenset(pair[0] for pair in templates)

    if len(templates) == 1:
        # there's only one template
        # avoid any further computation
        return templates[0][0]

    manual_template = request.GET.get('template')

    if manual_template and manual_template in template_names:
        return manual_template

    if request.current_page:
        return request.current_page.get_template()
    return get_cms_setting('TEMPLATES')[0][0]


def get_clean_username(user):
    try:
        username = force_text(user)
    except AttributeError:
        # AnonymousUser may not have USERNAME_FIELD
        username = "anonymous"
    else:
        # limit changed_by and created_by to avoid problems with Custom User Model
        if len(username) > PAGE_USERNAME_MAX_LENGTH:
            username = u'{0}... (id={1})'.format(
                username[:PAGE_USERNAME_MAX_LENGTH - 15],
                user.pk,
            )
    return username


def get_page_queryset(site, draft=True, published=False):
    from cms.models import Page

    if draft:
        return Page.objects.drafts().on_site(site)

    if published:
        return Page.objects.public().published(site)
    return Page.objects.public().on_site(site)


def get_page_from_path(site, path, preview=False, draft=False):
    """
    Resolves a url path to a single page object.
    Returns None if page does not exist
    """
    from cms.models import Title

    titles = Title.objects.select_related('page__node')
    published_only = (not draft and not preview)

    if draft:
        titles = titles.filter(publisher_is_draft=True)
    elif preview:
        titles = titles.filter(publisher_is_draft=False)
    else:
        titles = titles.filter(published=True, publisher_is_draft=False)
    titles = titles.filter(path=(path or ''))

    for title in titles.iterator():
        if title.page.node.site_id != site.pk:
            continue

        if published_only and not _page_is_published(title.page):
            continue

        title.page.title_cache = {title.language: title}
        return title.page
    return


def get_pages_from_path(site, path, preview=False, draft=False):
    """ Returns a queryset of pages corresponding to the path given
    """
    pages = get_page_queryset(
        site,
        draft=draft,
        published=not (draft or preview),
    )

    if path:
        # title_set__path=path should be clear, get the pages where the path of the
        # title object is equal to our path.
        return pages.filter(title_set__path=path).distinct()
    # if there is no path (slashes stripped) and we found a home, this is the
    # home page.
    return pages.filter(is_home=True).distinct()


def get_page_from_request(request, use_path=None, clean_path=None):
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
    from cms.utils.page_permissions import user_can_view_page_draft

    if hasattr(request, '_current_page_cache'):
        # The following is set by CurrentPageMiddleware
        return request._current_page_cache

    if clean_path is None:
        clean_path = not bool(use_path)

    draft = use_draft(request)
    preview = 'preview' in request.GET
    path = request.path_info if use_path is None else use_path

    if clean_path:
        pages_root = reverse("pages-root")

        if path.startswith(pages_root):
            path = path[len(pages_root):]

        # strip any final slash
        if path.endswith("/"):
            path = path[:-1]

    site = get_current_site()
    page = get_page_from_path(site, path, preview, draft)

    if draft and page and not user_can_view_page_draft(request.user, page):
        page = get_page_from_path(site, path, preview, draft=False)

    # For public pages, check if any parent is hidden due to published dates
    # In this case the selected page is not reachable
    if page and not draft:
        now = timezone.now()
        unpublished_ancestors = (
            page
            .get_ancestor_pages()
            .filter(
                Q(publication_date__gt=now)
                | Q(publication_end_date__lt=now),
            )
        )
        if unpublished_ancestors.exists():
            page = None
    return page


def get_all_pages_from_path(site, path, language):
    path = path.strip('/')
    pages = get_pages_from_path(site, path, draft=True)
    pages |= get_pages_from_path(site, path, preview=True, draft=False)
    return pages.filter(title_set__language=language)


def get_available_slug(site, path, language, suffix='copy', modified=False):
    """
    Generates slug for path.
    If path is used, appends the value of suffix to the end.
    """
    base, _, slug = path.rpartition('/')
    pages = get_all_pages_from_path(site, path, language)

    if pages.exists():
        match = SUFFIX_REGEX.match(slug)

        if match and modified:
            _next = int(match.groups()[-1]) + 1
            slug = SUFFIX_REGEX.sub('\g<1>-{}'.format(_next), slug)
        elif suffix:
            slug += '-' + suffix + '-2'
        else:
            slug += '-2'
        path = '%s/%s' % (base, slug) if base else slug
        return get_available_slug(site, path, language, suffix, modified=True)
    return slug
