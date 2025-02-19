from cms.utils import apphook_reload


class ApphookReloadMiddleware:
    """
    If the URLs are stale, reload them.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        apphook_reload.ensure_urlconf_is_up_to_date()
        return self.get_response(request)

    async def __acall__(self, request):
        apphook_reload.ensure_urlconf_is_up_to_date()
        return await self.get_response(request)

