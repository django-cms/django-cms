"""This is ugly, but seems there's no other way how to do what we need for
permission system.

This middleware is required only when CMS_PERMISSION = True.
"""

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from cms.utils.permissions import set_current_user

        set_current_user(getattr(request, 'user', None))
        return self.get_response(request)
