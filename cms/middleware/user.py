"""This is ugly, but seems there's no other way how to do what we need for
permission system.

This middleware is required only when CMS_PERMISSION = True.
"""
from cms.utils.permissions import set_current_user

class CurrentUserMiddleware(object):
    def process_request(self, request):
        set_current_user(getattr(request, 'user', None))