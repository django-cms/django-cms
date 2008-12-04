from cms.utils import get_site_from_request

class LazySite(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_site'):
            request._cached_site = get_site_from_request(request)
        return request._cached_site

class CurrentSiteMiddleware(object):
    def process_request(self, request):
        request.__class__.site = LazySite()
        return None
