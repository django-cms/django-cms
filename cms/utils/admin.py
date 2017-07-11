# -*- coding: utf-8 -*-
import json

from django.http import HttpResponse
from django.utils.encoding import smart_str


NOT_FOUND_RESPONSE = "NotFound"


def jsonify_request(response):
    """ Turn any response in a 200 response to let jQuery code handle it nicely.
        Response contains a json object with the following attributes:
         * status: original response status code
         * content: original response content
    """
    content = {'status': response.status_code, 'content': smart_str(response.content, response.charset)}
    return HttpResponse(json.dumps(content), content_type="application/json")
