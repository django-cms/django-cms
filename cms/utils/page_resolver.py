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
    """
    if 'django.contrib.admin' in settings.INSTALLED_APPS:
        admin_base = reverse('admin:index')
    else:
        admin_base = None
    pages_root = urllib.unquote(reverse("pages-root"))
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache
    page_queryset = get_page_queryset(request)
    site = Site.objects.get_current()
    if 'preview' in request.GET:
        pages = page_queryset.filter(site=site)
    else:
        pages = page_queryset.published().filter(site=site)
    if admin_base and request.path.startswith(admin_base):
        page_id = request.path.split('/')[0]
        try:
            page = pages.get(pk=page_id)
        except Page.DoesNotExist:
            return None
        request._current_page_cache = page
        return page
    if use_path:
        path = use_path
    else:
        path = request.path[len(pages_root):-1]
    if not pages.all_root():
        return None
    
    try:
        home = pages.get_home()
    except NoHomeFound:
        home = None
    if not path and home:
        page = home
        request._current_page_cache = page
        return page
    q = Q(title_set__path=path)
    if home:
        q |= Q(title_set__path='%s/%s' % (home.get_slug(), path))
        q &= Q(tree_id=home.tree_id)
    if settings.CMS_DBGETTEXT and settings.CMS_DBGETTEXT_SLUGS:
        # ugly hack -- brute force search for reverse path translation:
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