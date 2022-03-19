"""This is ugly, but seems there's no other way how to do what we need for
permission system.

This middleware is required only when CMS_PERMISSION = True.
"""
from django.utils.deprecation import MiddlewareMixin


class CurrentUserMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        from cms.utils.permissions import set_current_user

        set_current_user(getattr(request, 'user', None))

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response
