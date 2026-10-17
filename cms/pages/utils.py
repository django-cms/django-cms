import re

from django.urls import NoReverseMatch, reverse

from cms.compat import moved
from cms.utils import get_current_site, get_language_from_request
from cms.utils.conf import get_cms_setting

__getattr__, __dir__, __all__ = moved(
    __name__,
    {"get_clean_username": "cms.shared.users.get_clean_username"},
    since="6.0",
)

SUFFIX_REGEX = re.compile(r'^(.*)-(\d+)$')


def get_page_template_from_request(request):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    templates = get_cms_setting('TEMPLATES')
    template_names = frozenset(pair[0] for pair in templates)

    if not templates:
        # no templates defined, CMS is running headless
        return None

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
        try:
            pages_root = reverse("pages-root")
            if path.startswith(pages_root):
                path = path[len(pages_root):]

            # strip any final slash
            if path.endswith("/"):
                path = path[:-1]
        except NoReverseMatch:
            pass

    site = get_current_site(request)
    page_urls = (
        PageUrl
        .objects
        .get_for_site(site)
        .filter(path=path)
        .select_related("page", "page__site")
    )
    page_urls = list(page_urls.order_by("pk"))  # force queryset evaluation to save 1 query
    if not page_urls:
        return None
    # Paths are per language: another page may have the same path in another
    # language. The URL in the request's language wins.
    language = get_language_from_request(request)
    chosen = next((url for url in page_urls if url.language == language), page_urls[0])
    page = chosen.page
    if chosen.language == language:
        page.urls_cache = {url.language: url for url in page_urls if url.page_id == page.pk}
    return page


def get_available_slug(site, path, language, suffix='copy', modified=False):
    """
    Generates slug for path.
    If path is used, appends the value of suffix to the end.
    """
    from cms.pages.models.page import PageUrl

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
        path = f'{base}/{slug}' if base else slug
        return get_available_slug(site, path, language, suffix, modified=True)
    return slug


# Keep the module's existing exports alongside the relocated helpers.
__all__.extend(name for name in globals() if not name.startswith("_") and name != "moved")
__all__.sort()
