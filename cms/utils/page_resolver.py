from cms.exceptions import NoHomeFound
from cms.models.pagemodel import Page
from cms.utils.moderator import get_page_queryset
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
import urllib

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    ADMIN_BASE = reverse('admin:index')
else:
    ADMIN_BASE = None
PAGES_ROOT = urllib.unquote(reverse("pages-root"))


def get_page_from_request(request):
    """
    Gets the current page from a request object.
    """
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache
    page_queryset = get_page_queryset(request)
    site = Site.objects.get_current()
    if 'preview' in request.GET.keys():
        pages = page_queryset.filter(site=site)
    else:
        pages = page_queryset.published().filter(site=site)
    if ADMIN_BASE and request.path.startswith(ADMIN_BASE):
        page_id = request.path.split('/')[0]
        try:
            page = pages.get(pk=page_id)
        except Page.DoesNotExist:
            return None
        request._current_page_cache = page
        return page
    path = request.path[len(PAGES_ROOT):-1]
    if not pages.all_root():
        return None
    
    try:
        home = pages.get_home()
    except NoHomeFound:
        home = None
    if not path and home:
        request._current_page_cache = page
        return page
    q = Q(title_set__path=path)
    if home:
        q |= Q(title_set__path='%s/%s' % (home.get_slug(), path))
        q &= Q(tree_id=home.tree_id)
    try:
        page = pages.filter(q).distinct().get()
    except Page.DoesNotExist:
        return None
    request._current_page_cache = page
    return page