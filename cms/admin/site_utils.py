from django.contrib.sites.models import Site
from django.core.exceptions import (
    PermissionDenied,
)
from django.http import (
    Http404,
    HttpResponseRedirect,
)
from django.utils.translation import gettext as _

from cms.utils import get_current_site, page_permissions
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import add_url_parameters


def get_site_id_from_request(request):
    site_id = request.GET.get("site", request.session.get("cms_admin_site"))
    if site_id is None:
        return None

    try:
        return int(site_id)
    except ValueError:
        raise Http404(_("Invalid site ID."))


def get_site_from_request(request):
    site_id = get_site_id_from_request(request)
    if site_id is None:
        return get_current_site()
    try:
        return Site.objects._get_site_by_id(site_id)
    except Site.DoesNotExist:
        raise Http404(_("Site does not exist."))


def needs_site_redirect(request):
    user_sites = get_sites_for_user(request.user)
    if not user_sites:
        raise PermissionDenied(_("You do not have permission to view any sites. Please contact your administrator."))

    current_site = get_current_site()
    site_id = request.GET.get("site")
    legacy_session_site_id = request.session.get("cms_admin_site")
    if legacy_session_site_id and site_id is None:
        # Remove legacy session and possibly redirect with site query parameter
        del request.session["cms_admin_site"]
        if legacy_session_site_id == current_site.pk:
            return
        redirect_url = add_url_parameters(request.path, request.GET, site=legacy_session_site_id)
        return HttpResponseRedirect(redirect_url)

    # TODO: handle more cases?


def validate_site(request, site):
    user_sites = get_sites_for_user(request.user)
    if site not in user_sites:
        raise PermissionDenied(_("You do not have permission to view this site. Please contact your administrator."))


def get_site(request):
    """
    Validates the site from the request and returns it.
    If the user does not have permission to view any sites, raises PermissionDenied.
    """
    site = get_site_from_request(request)
    validate_site(request, site)
    return site


def get_sites_for_user(user):
    if hasattr(user, "_cms_user_sites"):
        return user._cms_user_sites

    sites = Site.objects.order_by("name")
    if not get_cms_setting("PERMISSION") or user.is_superuser:
        user._cms_user_sites = sites
        return sites

    _has_perm = page_permissions.user_can_change_at_least_one_page
    user_sites = [site for site in sites if _has_perm(user, site)]
    user._cms_user_sites = user_sites
    return user_sites
