from django.utils.functional import SimpleLazyObject


def get_page(request):
    from cms.appresolver import applications_page_check
    from cms.utils.page import get_page_from_request

    if not hasattr(request, '_current_page_cache'):
        request._current_page_cache = get_page_from_request(request)
        if not request._current_page_cache:
            # if this is in a apphook
            # find the page the apphook is attached to
            request._current_page_cache = applications_page_check(request)
    return request._current_page_cache


class CurrentPageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_page = SimpleLazyObject(lambda: get_page(request))
        return self.get_response(request)

    async def __acall__(self, request):
        request.current_page = SimpleLazyObject(lambda: get_page(request))
        return await self.get_response(request)
