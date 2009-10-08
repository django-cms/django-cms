"""
Debug Toolbar middleware
"""
from cms import settings as cms_settings
from django.conf import settings
from django.conf.urls.defaults import include, patterns
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode
import debug_toolbar.urls
from django.core.urlresolvers import reverse
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

    def show_toolbar(self, request, response):
        if request.is_ajax():
            return False
        if response.status_code != 200:
            return False 
        if not hasattr(request, "user"):
            return False
        if not request.user.is_authenticated() or not request.user.is_staff:
            return False
        if not response['Content-Type'].split(';')[0] in _HTML_TYPES:
            return False
        if request.path_info.startswith(reverse("admin:index")):
            return False
        if not request.current_page:
            return False
        return True

    def process_response(self, request, response):
        if self.show_toolbar(request, response):
            response.content = replace_insensitive(smart_unicode(response.content), u'<body>', '<body>' + smart_unicode(self.render_toolbar(request) ))
        return response
    
    def render_toolbar(self, request):
        """
        Renders the Toolbar.
        """
        page = request.current_page
        
        return render_to_string('cms/toolbar/toolbar.html', {
            'page':page,
            'edit':"edit" in request.GET,
            'CMS_MEDIA_URL': cms_settings.CMS_MEDIA_URL,
        })

