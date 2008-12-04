"""Base DebugPanel class"""

class DebugPanel(object):
    """
    Base class for debug panels.
    """
    # name = Base
    
    has_content = True
    
    def __init__(self, request):
        self.request = request

    def process_request(self, request):
        return None
    
    def process_response(self, request, response):
        return response
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        return None

    def dom_id(self):
        return 'djDebug%sPanel' % (self.name.replace(' ', ''))

    def title(self):
        raise NotImplementedError

    def url(self):
        raise NotImplementedError

    def content(self):
        # TODO: This is a bit flaky in that panel.content() returns a string 
        # that gets inserted into the toolbar HTML template.
        raise NotImplementedError
