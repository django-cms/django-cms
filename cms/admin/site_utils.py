from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _

from cms.utils import get_current_site, get_sites_for_user
from cms.utils.urlutils import add_url_parameters


def needs_site_redirect(request):
    user_sites = get_sites_for_user(request.user)
    if not user_sites:
        raise PermissionDenied(_("You do not have permission to view any sites. Please contact your administrator."))

    current_site = get_current_site(request)
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
