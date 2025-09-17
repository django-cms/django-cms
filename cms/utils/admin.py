from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from cms.utils import page_permissions
from cms.utils.conf import get_cms_setting

NOT_FOUND_RESPONSE = "NotFound"


def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    content = {'status': response.status_code, 'content': smart_str(response.content, response.charset)}
    return JsonResponse(content)


def _get_site_id_from_request(request):
    site_id = request.GET.get("site", request.session.get("cms_admin_site"))
    if site_id is None:
        return None

    try:
        return int(site_id)
    except ValueError:
        raise Http404(_("Invalid site ID."))


def get_site_from_request(request):
    site_id = _get_site_id_from_request(request)
    if site_id is None:
        from cms.utils import get_current_site

        return get_current_site(request)
    try:
        from django.contrib.sites.models import Site

        return Site.objects._get_site_by_id(site_id)
    except Site.DoesNotExist:
        raise Http404(_("Site does not exist."))
