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
from cms.utils.admin import get_admin_menu_item_context
from cms.utils.plugins import get_placeholders
from django.template.defaultfilters import title, safe
from cms.plugin_pool import plugin_pool
from django.utils import simplejson
from django.http import HttpResponseRedirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.http import urlquote
import os



_HTML_TYPES = ('text/html', 'application/xhtml+xml')

def inster_after_tag(string, tag, insertion):
    no_case = string.lower()
    index = no_case.find("<%s" % tag.lower())
    if index:
        start_tag = index
        end_tag = start_tag + no_case[start_tag:].find(">") + 1
        return string[:end_tag] + insertion + string[end_tag:]
    else:
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
    
    def process_request(self, request):
        print "hello"
        print request.GET
        if "edit" in request.GET and not request.user.is_authenticated():
            tup=(settings.LOGIN_URL, REDIRECT_FIELD_NAME, urlquote(request.get_full_path()))
            return HttpResponseRedirect('%s?%s=%s' % tup)
            

    def process_response(self, request, response):
        if self.show_toolbar(request, response):
            response.content = inster_after_tag(smart_unicode(response.content), u'body', smart_unicode(self.render_toolbar(request)))
        return response

    def render_toolbar(self, request):
        """
        Renders the Toolbar.
        """
        edit = "edit" in request.GET
        page = request.current_page
        move_dict = []
        if edit:
            placeholders = get_placeholders(request)
            for placeholder in placeholders:
                d = {}
                if placeholder in settings.CMS_PLACEHOLDER_CONF and "name" in settings.CMS_PLACEHOLDER_CONF[placeholder]:
                    d['name'] =  title(settings.CMS_PLACEHOLDER_CONF[placeholder]["name"])
                else:
                    d['name'] =  title(placeholder)
                plugins = plugin_pool.get_all_plugins(placeholder)
                d['plugins'] = [] 
                for p in plugins:
                    d['plugins'].append(p.value)
                d['type'] = placeholder
                move_dict.append(d)
            data = safe(simplejson.dumps(move_dict))
        else:
            data = {}
        context = get_admin_menu_item_context(request, page, filtered=False)
        context.update({
            'page':page,
            'placeholder_data':data,
            'edit':edit,
            'CMS_MEDIA_URL': cms_settings.CMS_MEDIA_URL,
        })
        return render_to_string('cms/toolbar/toolbar.html', context )

