"""Middleware used by Reversion."""


import sys

from reversion.revisions import revision


class RevisionMiddleware(object):
    
    """Wraps the entire request in a Revision."""
    
    def process_request(self, request):
        """Starts a new revision."""
        revision.start()
        if request.user.is_authenticated():
            revision.user = request.user
        
    def process_response(self, request, response):
        """Closes the revision."""
        if revision.is_active():
            revision.end()
        return response
        
    def process_exception(self, request, exception):
        """Closes the revision."""
        revision.invalidate()