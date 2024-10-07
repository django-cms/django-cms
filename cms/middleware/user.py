"""This is ugly, but seems there's no other way how to do what we need for
permission system.

This middleware is required only when CMS_PERMISSION = True.
"""
from django.utils.deprecation import MiddlewareMixin


class CurrentUserMiddleware(MiddlewareMixin):
    async_capable = False

    def process_request(self, request):
        from cms.utils.permissions import set_current_user

        set_current_user(getattr(request, 'user', None))
