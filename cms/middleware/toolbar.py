"""
Debug Toolbar middleware
"""
from cms import settings as cms_settings
from django.conf import settings
from django.conf.urls.defaults import include, patterns
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode
import debug_toolbar.urls
import os



_HTML_TYPES = ('text/html', 'application/xhtml+xml')

def replace_insensitive(string, target, replacement):
    """
    Similar to string.replace() but is case insensitive
    Code borrowed from: http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else: # no results so return the original string
        return string

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar on incoming request and render toolbar
    on outgoing response.
    """
    def __init__(self):
        self.debug_toolbar = None
        #self.original_pattern = patterns('', ('', include(self.original_urlconf)),)
        #self.override_url = True

        # Set method to use to decide to show toolbar
        self.show_toolbar = self._show_toolbar # default

    def _show_toolbar(self, request):
        if request.is_ajax() and not \
            request.path.startswith(os.path.join('/', debug_toolbar.urls._PREFIX)):
            # Allow ajax requests from the debug toolbar
            return False 
        if not request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS:
            return False
        return True

    def process_request(self, request):
        if self.show_toolbar(request):
            #if self.override_url:
            #    debug_toolbar.urls.urlpatterns += self.original_pattern
            #    self.override_url = False
            #request.urlconf = 'debug_toolbar.urls'

            #self.debug_toolbar = DebugToolbar(request)
            #for panel in self.debug_toolbar.panels:
            #    panel.process_request(request)
            pass
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self.debug_toolbar:
            for panel in self.debug_toolbar.panels:
                panel.process_view(request, view_func, view_args, view_kwargs)

    def process_response(self, request, response):
        print request.user
        if not request.user.is_authenticated() or not request.user.is_staff:
            return response
        if response.status_code != 200:
            return response
        if response['Content-Type'].split(';')[0] in _HTML_TYPES:
            response.content = replace_insensitive(smart_unicode(response.content), u'</body>', smart_unicode(self.render_toolbar(request) + u'</body>'))
        return response
    
    def render_toolbar(self, request):
        """
        Renders the Toolbar.
        """
        return render_to_string('cms/toolbar.html', {
            
            'CMS_MEDIA_URL': cms_settings.CMS_MEDIA_URL,
        })

