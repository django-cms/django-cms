"""This is ugly, but seems there's no other way how to do what we need for
permission system.

This middleware is required only when CMS_PERMISSION = True.
"""


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from cms.utils.permissions import reset_current_user, set_current_user

        token = set_current_user(getattr(request, 'user', None))
        try:
            return self.get_response(request)
        finally:
            # Reset at the request boundary so the current user does not leak
            # into the next request handled by a reused worker thread.
            reset_current_user(token)
