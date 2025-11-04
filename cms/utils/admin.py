from django.contrib.sites.models import Site
from django.forms import IntegerField, ValidationError
from django.http import Http404, JsonResponse
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from cms.utils import get_current_site

NOT_FOUND_RESPONSE = "NotFound"


def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    content = {'status': response.status_code, 'content': smart_str(response.content, response.charset)}
    return JsonResponse(content)


def get_site_from_request(request):
    try:
        site_id = request.GET.get("site") or request.POST.get("site")
        site_id = IntegerField().clean(site_id)
        site = Site.objects.get(pk=site_id)
    except (ValidationError, Site.DoesNotExist):
        site = get_current_site(request)

    return site
