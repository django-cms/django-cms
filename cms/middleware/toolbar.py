"""
Edit Toolbar middleware
"""
from cms import settings as cms_settings
from cms.utils import get_template_from_request
from cms.utils.plugins import get_placeholders
from cms.utils.urlutils import is_media_request
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.context import RequestContext
from django.template.defaultfilters import title, safe
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

HTML_TYPES = ('text/html', 'application/xhtml+xml')

def inster_after_tag(string, tag, insertion):
    no_case = string.lower()
    index = no_case.find("<%s" % tag.lower())
    if index > -1:
        start_tag = index
        end_tag = start_tag + no_case[start_tag:].find(">") + 1
        return string[:end_tag] + insertion + string[end_tag:]
    else:
        return string

def toolbar_plugin_processor(instance, placeholder, rendered_content, original_context):
    return '<div id="cms_plugin_%s_%s" class="cms_plugin_holder" rel="%s" type="%s">%s</div>' % \
        (instance.placeholder.id, instance.pk, instance.placeholder.slot, instance.plugin_type, rendered_content)

class ToolbarMiddleware(object):
    """
    Middleware to set up CMS Toolbar.
    """

    def show_toolbar(self, request, response):
        if request.is_ajax():
            return False
        if response.status_code != 200:
            return False
        if not response['Content-Type'].split(';')[0] in HTML_TYPES:
            return False
        try:
            if request.path.startswith(reverse("admin:index")):
                return False
        except NoReverseMatch:
            pass
        if is_media_request(request):
            return False
        if "edit" in request.GET:
            return True
        if not hasattr(request, "user"):
            return False
        if not request.user.is_authenticated() or not request.user.is_staff:
            return False
        return True

    def process_request(self, request):
        if request.method == "POST":
            if "edit" in request.GET and "cms_username" in request.POST:
                user = authenticate(username=request.POST.get('cms_username', ""), password=request.POST.get('cms_password', ""))
                if user:
                    login(request, user)
            if request.user.is_authenticated() and "logout_submit" in request.POST:
                logout(request)
                request.POST = {}
                request.method = 'GET'
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
        auth = request.user.is_staff or request.user.is_superuser
        edit = request.session.get('cms_edit', False) and auth
        page = request.current_page
        move_dict = []
        if edit and page:
            template = get_template_from_request(request)
            placeholders = get_placeholders(template)
            for placeholder in placeholders:
                d = {}
                name = cms_settings.CMS_PLACEHOLDER_CONF.get("%s %s" % (page.get_template(), placeholder), {}).get("name", None)
                if not name:
                    name = cms_settings.CMS_PLACEHOLDER_CONF.get(placeholder, {}).get("name", None)
                if not name:
                    name = title(placeholder)
                else:
                    name = _(name)
                d['name'] = name
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
            context = {}
        context.update({
            'auth':auth,
            'page':page,
            'templates': cms_settings.CMS_TEMPLATES,
            'auth_error':not auth and 'cms_username' in request.POST,
            'placeholder_data':data,
            'edit':edit,
            'moderator': cms_settings.CMS_MODERATOR,
            'CMS_MEDIA_URL': cms_settings.CMS_MEDIA_URL,
        })
        #from django.core.context_processors import csrf
        #context.update(csrf(request))
        return render_to_string('cms/toolbar/toolbar.html', context, RequestContext(request))
