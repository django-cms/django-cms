"""
Edit Toolbar middleware
"""
from cms import settings as cms_settings
from cms.utils.plugins import get_placeholders
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.template.context import Context
from django.template.defaultfilters import title, safe
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.encoding import smart_unicode

_HTML_TYPES = ('text/html', 'application/xhtml+xml')

def inster_after_tag(string, tag, insertion):
    no_case = string.lower()
    index = no_case.find("<%s" % tag.lower())
    if index > -1:
        start_tag = index
        end_tag = start_tag + no_case[start_tag:].find(">") + 1
        return string[:end_tag] + insertion + string[end_tag:]
    else:
        return string

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def show_toolbar(self, request, response):
        if request.is_ajax():
            return False
        if response.status_code != 200:
            return False 
        if not response['Content-Type'].split(';')[0] in _HTML_TYPES:
            return False
        if request.path_info.startswith(reverse("admin:index")):
            return False
        if "edit" in request.GET:
            return True
        if not hasattr(request, "user"):
            return False
        if not request.user.is_authenticated() or not request.user.is_staff:
            return False
        return True
    
    def process_request(self, request):
        if request.method == "POST" and "edit" in request.GET and "cms_username" in request.POST:
            user = authenticate(username=request.POST.get('cms_username', ""), password=request.POST.get('cms_password', ""))
            if user:
                login(request, user)
        if request.user.is_authenticated() and request.user.is_staff:
            if "edit-off" in request.GET:
                request.session['cms_edit'] = False
            if "edit" in request.GET:
                request.session['cms_edit'] = True

    def process_response(self, request, response):
        if self.show_toolbar(request, response):
            response.content = inster_after_tag(smart_unicode(response.content), u'body', smart_unicode(self.render_toolbar(request)))
        return response

    def render_toolbar(self, request):
        from cms.plugin_pool import plugin_pool
        from cms.utils.admin import get_admin_menu_item_context
        """
        Renders the Toolbar.
        """
        auth = request.user.is_authenticated() and request.user.is_staff
        edit = request.session.get('cms_edit', False) and auth
        page = request.current_page
        move_dict = []
        if edit and page:
            placeholders = get_placeholders(request)
            for placeholder in placeholders:
                d = {}
                name = cms_settings.CMS_PLACEHOLDER_CONF.get("%s %s" % (page.get_template(), placeholder), {}).get("name", None)
                if not name:
                    name = cms_settings.CMS_PLACEHOLDER_CONF.get(placeholder, {}).get("name", None)
                if not name:
                    name = placeholder
                d['name'] = title(name)
                plugins = plugin_pool.get_all_plugins(placeholder, page)
                d['plugins'] = [] 
                for p in plugins:
                    d['plugins'].append(p.value)
                d['type'] = placeholder
                move_dict.append(d)
            data = safe(simplejson.dumps(move_dict))
        else:
            data = {}
        if auth and page:
            context = get_admin_menu_item_context(request, page, filtered=False)
        else:
            context = Context()
        context.update({
            'auth':auth,
            'page':page,
            'templates': cms_settings.CMS_TEMPLATES,
            'auth_error':not auth and 'cms_username' in request.POST,
            'placeholder_data':data,
            'edit':edit,
            'CMS_MEDIA_URL': cms_settings.CMS_MEDIA_URL,
        })
        return render_to_string('cms/toolbar/toolbar.html', context )

