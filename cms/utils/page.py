import re

from django.urls import reverse
from django.utils.encoding import force_str

from cms.constants import PAGE_USERNAME_MAX_LENGTH
from cms.utils import get_current_site
from cms.utils.conf import get_cms_setting

SUFFIX_REGEX = re.compile(r'^(.*)-(\d+)$')


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
        username = force_str(user)
    except AttributeError:
        # AnonymousUser may not have USERNAME_FIELD
        username = "anonymous"
    else:
        # limit changed_by and created_by to avoid problems with Custom User Model
        if len(username) > PAGE_USERNAME_MAX_LENGTH:
            username = f'{username[:PAGE_USERNAME_MAX_LENGTH - 15]}... (id={user.pk})'
    return username


def get_page_queryset(site, draft=True, published=False):
    from cms.models import Page

    return Page.objects.on_site(site)


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
    from cms.models import PageUrl

    if hasattr(request, '_current_page_cache'):
        # The following is set by CurrentPageMiddleware
        return request._current_page_cache

    if clean_path is None:
        clean_path = not bool(use_path)

    path = request.path_info if use_path is None else use_path

    if clean_path:
        pages_root = reverse("pages-root")

        if path.startswith(pages_root):
            path = path[len(pages_root):]

        # strip any final slash
        if path.endswith("/"):
            path = path[:-1]

    site = get_current_site()
    page_urls = (
        PageUrl
        .objects
        .get_for_site(site)
        .filter(path=path)
        .select_related('page__node')
    )
    page_urls = list(page_urls)  # force queryset evaluation to save 1 query
    try:
        page = page_urls[0].page
    except IndexError:
        page = None
    else:
        page.urls_cache = {url.language: url for url in page_urls}
    return page


def get_available_slug(site, path, language, suffix='copy', modified=False):
    """
    Generates slug for path.
    If path is used, appends the value of suffix to the end.
    """
    from cms.models.pagemodel import PageUrl

    base, _, slug = path.rpartition('/')
    page_urls = PageUrl.objects.get_for_site(site, path=path, language=language)

    if page_urls.exists():
        match = SUFFIX_REGEX.match(slug)

        if match and modified:
            _next = int(match.groups()[-1]) + 1
            slug = SUFFIX_REGEX.sub(f'\\g<1>-{_next}', slug)
        elif suffix:
            slug += '-' + suffix + '-2'
        else:
            slug += '-2'
        path = '%s/%s' % (base, slug) if base else slug
        return get_available_slug(site, path, language, suffix, modified=True)
    return slug
