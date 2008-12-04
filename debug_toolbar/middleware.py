"""
Debug Toolbar middleware
"""
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.views.static import serve
from django.http import Http404
from debug_toolbar.toolbar.loader import DebugToolbar
from debug_toolbar.stats import enable_tracking, reset_tracking, freeze_tracking
try: import cStringIO as StringIO
except ImportError: import StringIO
import os.path

_HTML_TYPES = ('text/html', 'application/xhtml+xml')

def replace_insensitive(string, target, replacement):
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index != -1:
        result = string[:index] + replacement + string[index + len(target):]
        return result
    # no results so return the original string
    return string

class DebugToolbarMiddleware(object):
    """
    Middleware to set up Debug Toolbar on incoming request and render toolbar
    on outgoing response.
    """
    def __init__(self):
        self.debug_toolbar = None

    def show_toolbar(self, request, response=None):
        if not settings.DEBUG:
            return False
        if not getattr(settings, 'DEBUG_TOOLBAR', True):
            return False
        if (not request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS) and \
                (request.user.is_authenticated() and not request.user.is_superuser):
            return False
        if response:
            if getattr(response, 'skip_debug_response', False):
                return False
            if response.status_code >= 300 and response.status_code < 400:
                return False
        return True

    def static_serve(self, request, fname):
        return serve(request, fname, os.path.join(os.path.dirname(__file__), 'media'))
        
    def process_request(self, request):
        reset_tracking()
        if self.show_toolbar(request):
            # Enable statistics tracking
            if request.GET.get('djDebugStatic'):
                return self.static_serve(request, request.GET['djDebugStatic'])
            if not request.is_ajax():
                enable_tracking(True)
            self.debug_toolbar = DebugToolbar(request)
            self.debug_toolbar.load_panels()
            debug = request.GET.get('djDebug')
            # kinda ugly, needs changes to the loader to optimize
            response = None
            for panel in self.debug_toolbar.panels:
                if debug == panel.name:
                    response = panel.process_ajax(request)
                if not response and not request.is_ajax():
                    response = panel.process_request(request)
                if response:
                    response.skip_debug_response = True
                    return response

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # TODO: this doesn't handle multiples yet
        if self.show_toolbar(request) and not request.is_ajax():
            new_callback = None
            for panel in self.debug_toolbar.panels:
                response = panel.process_view(request, callback, callback_args, callback_kwargs)
                if response:
                    return response

    def process_response(self, request, response):
        if self.show_toolbar(request, response) and not request.is_ajax():
            freeze_tracking()
            if response['Content-Type'].split(';')[0] in _HTML_TYPES:
                # Saving this here in case we ever need to inject into <head>
                #response.content = _END_HEAD_RE.sub(smart_str(self.debug_toolbar.render_styles() + "%s" % match.group()), response.content)
                for panel in self.debug_toolbar.panels:
                    nr = panel.process_response(request, response)
                    # Incase someone forgets `return response`
                    if nr: response = nr
                response.content = replace_insensitive(smart_unicode(response.content), u'</body>', smart_unicode(self.debug_toolbar.render_toolbar()) + u'</body>')
        return response