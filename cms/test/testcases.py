# -*- coding: utf-8 -*-
from cms.admin.forms import save_permissions
from cms.models import Title, Page
from cms.models.moderatormodels import ACCESS_PAGE_AND_DESCENDANTS
from cms.models.permissionmodels import PagePermission, PageUser
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.test.util.context_managers import UserLoginContext, SettingsOverride
from cms.utils.permissions import _thread_locals
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import reverse
from django.template.context import Context
from django.template.defaultfilters import slugify
from django.test.testcases import TestCase
from menus.menu_pool import menu_pool
from urlparse import urlparse
import sys
import urllib
import warnings


URL_CMS_PAGE = "/admin/cms/page/"
URL_CMS_PAGE_ADD = URL_CMS_PAGE + "add/"
URL_CMS_PAGE_CHANGE = URL_CMS_PAGE + "%d/" 
URL_CMS_PAGE_DELETE = URL_CMS_PAGE_CHANGE + "delete/" 
URL_CMS_PLUGIN_ADD = URL_CMS_PAGE + "add-plugin/"
URL_CMS_PLUGIN_EDIT = URL_CMS_PAGE + "edit-plugin/"
URL_CMS_PLUGIN_REMOVE = URL_CMS_PAGE + "remove-plugin/"
URL_CMS_TRANSLATION_DELETE = URL_CMS_PAGE_CHANGE + "delete-translation/"

class _Warning(object):
    def __init__(self, message, category, filename, lineno):
        self.message = message
        self.category = category
        self.filename = filename
        self.lineno = lineno



def _collectWarnings(observeWarning, f, *args, **kwargs):
    def showWarning(message, category, filename, lineno, file=None, line=None):
        assert isinstance(message, Warning)
        observeWarning(_Warning(
                message.args[0], category, filename, lineno))

    # Disable the per-module cache for every module otherwise if the warning
    # which the caller is expecting us to collect was already emitted it won't
    # be re-emitted by the call to f which happens below.
    for v in sys.modules.itervalues():
        if v is not None:
            try:
                v.__warningregistry__ = None
            except:
                # Don't specify a particular exception type to handle in case
                # some wacky object raises some wacky exception in response to
                # the setattr attempt.
                pass

    origFilters = warnings.filters[:]
    origShow = warnings.showwarning
    warnings.simplefilter('always')
    try:
        warnings.showwarning = showWarning
        result = f(*args, **kwargs)
    finally:
        warnings.filters[:] = origFilters
        warnings.showwarning = origShow
    return result

class CMSTestCase(TestCase):
    counter = 1
        
    def _post_teardown(self):
        # Needed to clean the menu keys cache, see menu.menu_pool.clear()
        menu_pool.clear()
        super(CMSTestCase, self)._post_teardown()
        
    def login_user(self, user):
        logged_in = self.client.login(username=user.username, password=user.username)
        self.user = user
        self.assertEqual(logged_in, True)
        
    def login_user_context(self, user):
        return UserLoginContext(self, user)
        
    def get_superuser(self):
        admin = User(username="admin", is_staff=True, is_active=True, is_superuser=True)
        admin.set_password("admin")
        admin.save()
        return admin
    
    def get_new_page_data(self, parent_id=''):
        page_data = {'title':'test page %d' % self.counter, 
            'slug':'test-page-%d' % self.counter, 'language':settings.LANGUAGES[0][0],
            'site':1, 'template':'nav_playground.html', 'parent': parent_id}
        
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        
        self.counter = self.counter + 1
        return page_data
    
    def print_page_structure(self, title=None):
        """Just a helper to see the page struct.
        """
        for page in Page.objects.drafts().order_by('tree_id', 'lft'):
            print "%s%s #%d" % ("    " * (page.level), page, page.id)
    
    def print_node_structure(self, nodes, *extra):
        def _rec(nodes, level=0):
            ident = level * '    '
            for node in nodes:
                raw_attrs = [(bit, getattr(node, bit, node.attr.get(bit, "unknown"))) for bit in extra]
                attrs = ', '.join(['%s: %r' % data for data in raw_attrs])
                print "%s%s: %s" % (ident, node.title, attrs)
                _rec(node.children, level+1)
        _rec(nodes)
    
    def assertObjectExist(self, qs, **filter):
        try:
            return qs.get(**filter) 
        except ObjectDoesNotExist:
            pass
        raise self.failureException, "ObjectDoesNotExist raised"
    
    def assertObjectDoesNotExist(self, qs, **filter):
        try:
            qs.get(**filter) 
        except ObjectDoesNotExist:
            return
        raise self.failureException, "ObjectDoesNotExist not raised"
    
    def create_page(self, parent_page=None, user=None, position="last-child", 
            title=None, site=1, published=False, in_navigation=False,
            moderate=False, language=None, title_extra=None, **extra):
        """
        Common way for page creation with some checks
        """
        _thread_locals.user = user
        if not language:
            language = settings.LANGUAGES[0][0]
            if settings.CMS_SITE_LANGUAGES.get(site, False):
                language = settings.CMS_SITE_LANGUAGES[site][0]
        site = Site.objects.get(pk=site)
        
        page_data = {
            'site': site,
            'template': 'nav_playground.html',
            'published': published,
            'in_navigation': in_navigation,
        }
        if user:
            page_data['created_by'] = user
            page_data['changed_by'] = user
        if parent_page:
            page_data['parent'] = parent_page
        page_data.update(extra)

        page = Page(**page_data)
        if parent_page:
            page.insert_at(self.reload(parent_page), position)
        page.save()

        if settings.CMS_MODERATOR and user:
            page.pagemoderator_set.create(user=user)
        
        if not title:
            title = 'test page %d' % self.counter
            slug = 'test-page-%d' % self.counter
        else:
            slug = slugify(title)
        self.counter = self.counter + 1
        if not title_extra:
            title_extra = {}
        self.create_title(
            title=title,
            slug=slug,
            language=language,
            page=page,
            **title_extra
        )
            
        del _thread_locals.user
        return page
    
    def create_title(self, title, slug, language, page, **extra):
        return Title.objects.create(
            title=title,
            slug=slug,
            language=language,
            page=page,
            **extra
        )

    def copy_page(self, page, target_page):
        from cms.utils.page import get_available_slug
        
        data = {
            'position': 'last-child',
            'target': target_page.pk,
            'site': 1,
            'copy_permissions': 'on',
            'copy_moderation': 'on',
        }
        
        response = self.client.post(URL_CMS_PAGE + "%d/copy-page/" % page.pk, data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "ok")
        
        title = page.title_set.all()[0] 
        copied_slug = get_available_slug(title)
        
        copied_page = self.assertObjectExist(Page.objects, title_set__slug=copied_slug, parent=target_page)
        return copied_page
    
    def move_page(self, page, target_page, position="first-child"):       
        page.move_page(target_page, position)
        return self.reload_page(page)
        
    def reload_page(self, page):
        """
        Returns a fresh instance of the page from the database
        """
        return self.reload(page)
    
    def reload(self, obj):
        return obj.__class__.objects.get(pk=obj.pk)
    
    def get_pages_root(self):
        return urllib.unquote(reverse("pages-root"))
        
    def get_context(self, path=None):
        if not path:
            path = self.get_pages_root()
        context = {}
        request = self.get_request(path)
        
        context['request'] = request
        
        return Context(context)   
        
    def get_request(self, path=None, language=settings.LANGUAGES[0][0]):
        if not path:
            path = self.get_pages_root()
        
        parsed_path = urlparse(path)
        host = parsed_path.netloc or 'testserver'
        port = 80
        if ':' in host:
            host, port = host.split(':', 1)
        
        environ = {
            'HTTP_COOKIE':       self.client.cookies,
            'PATH_INFO':         parsed_path.path,
            'QUERY_STRING':      parsed_path.query,
            'REMOTE_ADDR':       '127.0.0.1',
            'REQUEST_METHOD':    'GET',
            'SCRIPT_NAME':       '',
            'SERVER_NAME':       host,
            'SERVER_PORT':       port,
            'SERVER_PROTOCOL':   'HTTP/1.1',
            'wsgi.version':      (1,0),
            'wsgi.url_scheme':   'http',
            'wsgi.errors':       self.client.errors,
            'wsgi.multiprocess': True,
            'wsgi.multithread':  False,
            'wsgi.run_once':     False,
            'wsgi.input':        ''
        }
        request = WSGIRequest(environ)
        request.session = self.client.session
        request.user = getattr(self, 'user', AnonymousUser())
        request.LANGUAGE_CODE = language
        return request
    
    def create_page_user(self, username, password=None, 
        can_add_page=True, can_change_page=True, can_delete_page=True, 
        can_recover_page=True, can_add_pageuser=True, can_change_pageuser=True, 
        can_delete_pageuser=True, can_add_pagepermission=True, 
        can_change_pagepermission=True, can_delete_pagepermission=True,
        grant_all=False):
        """
        Helper function for creating page user, through form on:
            /admin/cms/pageuser/add/
            
        Returns created user.
        """
        if grant_all:
            return self.create_page_user(username, password, 
                True, True, True, True, True, True, True, True, True, True)
            
        if password is None:
            password=username
        
        data = {
            'can_add_page': can_add_page, 
            'can_change_page': can_change_page, 
            'can_delete_page': can_delete_page, 
            'can_recover_page': can_recover_page, 
            'can_add_pageuser': can_add_pageuser, 
            'can_change_pageuser': can_change_pageuser, 
            'can_delete_pageuser': can_delete_pageuser, 
            'can_add_pagepermission': can_add_pagepermission,
            'can_change_pagepermission': can_change_pagepermission,
            'can_delete_pagepermission': can_delete_pagepermission,
        }
        if hasattr(self, 'user'):
            created_by = self.user
        else:
            created_by = User.objects.create_superuser('superuser', 'superuser@django-cms.org', 'superuser')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, 'username@django-cms.org', password)
            user.is_staff = True
            user.is_active = True
        page_user = PageUser(created_by=created_by)
        for field in [f.name for f in User._meta.local_fields]:
            setattr(page_user, field, getattr(user, field))
        user.save()
        page_user.save()
        save_permissions(data, page_user)
        return user
        
    def assign_user_to_page(self, page, user, grant_on=ACCESS_PAGE_AND_DESCENDANTS,
        can_add=False, can_change=False, can_delete=False, 
        can_change_advanced_settings=False, can_publish=False, 
        can_change_permissions=False, can_move_page=False, can_moderate=False, 
        grant_all=False):
        """Assigns given user to page, and gives him requested permissions. 
        
        Note: this is not happening over frontend, maybe a test for this in 
        future will be nice.
        """
        if grant_all:
            return self.assign_user_to_page(page, user, grant_on, 
                True, True, True, True, True, True, True, True)
        
        data = {
            'can_add': can_add,
            'can_change': can_change,
            'can_delete': can_delete, 
            'can_change_advanced_settings': can_change_advanced_settings,
            'can_publish': can_publish, 
            'can_change_permissions': can_change_permissions, 
            'can_move_page': can_move_page, 
            'can_moderate': can_moderate,  
        }
        
        page_permission = PagePermission(page=page, user=user, grant_on=grant_on, **data)
        page_permission.save()
        return page_permission
    
    def add_plugin(self, user=None, page=None, placeholder=None, language='en', body=''):
        if not placeholder:
            if page:
                placeholder = page.placeholders.get(slot__iexact='Right-Column')
            else:
                placeholder = page.placeholders.get(slot__iexact='Right-Column')
            
        plugin_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder, 
            position=1, 
            language=language
        )
        plugin_base.insert_at(None, position='last-child', save=False)
                
        plugin = Text(body=body)
        plugin_base.set_base_attr(plugin)
        plugin.save()
        return plugin.pk
    
    def publish_page(self, page, approve=False, user=None, published_check=True):
        if user:
            self.login_user(user)
        
        if published_check and not approve:
            # must have public object now
            self.assertFalse(page.publisher_public)
            self.assertFalse(page.published)
            
        # publish / approve page by master
        response = self.client.post(URL_CMS_PAGE + "%d/change-status/" % page.pk, {1 :1})
        self.assertEqual(response.status_code, 200)
        
        if not approve:
            page = self.reload_page(page)
            if published_check:
                # must have public object now
                self.assertTrue(page.publisher_public, "Page '%s' has no publisher_public" % page)
                # and public object must be published
                self.assertTrue(page.publisher_public.published)
            return page
        
        # approve
        page = self.approve_page(page)
        if published_check:
            # must have public object now
            self.assertTrue(page.publisher_public, "Page '%s' has no publisher_public" % page)
            # and public object must be published
            self.assertTrue(page.publisher_public.published)
        
        return page
    
    def approve_page(self, page):
        response = self.client.get(URL_CMS_PAGE + "%d/approve/" % page.pk)
        self.assertRedirects(response, URL_CMS_PAGE)
        # reload page
        return self.reload_page(page)
    
    def check_published_page_attributes(self, page):
        public_page = page.publisher_public
        
        if page.parent:
            self.assertEqual(page.parent_id, public_page.parent.publisher_draft.id)
        
        self.assertEqual(page.level, public_page.level)
        
        # TODO: add check for siblings
        
        draft_siblings = list(page.get_siblings(True). \
            filter(publisher_is_draft=True).order_by('tree_id', 'parent', 'lft'))
        public_siblings = list(public_page.get_siblings(True). \
            filter(publisher_is_draft=False).order_by('tree_id', 'parent', 'lft'))
        
        skip = 0
        for i, sibling in enumerate(draft_siblings):
            if not sibling.publisher_public_id:
                skip += 1
                continue
            self.assertEqual(sibling.id, public_siblings[i - skip].publisher_draft.id) 
    
    def request_moderation(self, page, level):
        """Assign current logged in user to the moderators / change moderation
        
        Args:
            page: Page on which moderation should be changed
        
            level <0, 7>: Level of moderation, 
                1 - moderate page
                2 - moderate children
                4 - moderate descendants
                + conbinations
        """
        response = self.client.post("/admin/cms/page/%d/change-moderation/" % page.id, {'moderate': level})
        self.assertEquals(response.status_code, 200)
        
    def failUnlessWarns(self, category, message, f, *args, **kwargs):
        warningsShown = []
        result = _collectWarnings(warningsShown.append, f, *args, **kwargs)

        if not warningsShown:
            self.fail("No warnings emitted")
        first = warningsShown[0]
        for other in warningsShown[1:]:
            if ((other.message, other.category)
                != (first.message, first.category)):
                self.fail("Can't handle different warnings")
        self.assertEqual(first.message, message)
        self.assertTrue(first.category is category)

        return result
    assertWarns = failUnlessWarns


class SettingsOverrideTestCase(CMSTestCase):
    settings_overrides = {}
    
    def _pre_setup(self):
        self._enter_settings_override()
        super(SettingsOverrideTestCase, self)._pre_setup()
        
    def _enter_settings_override(self):
        self._settings_ctx_manager = SettingsOverride(**self.settings_overrides)
        self._settings_ctx_manager.__enter__()
        
    def _post_teardown(self):
        super(SettingsOverrideTestCase, self)._post_teardown()
        self._exit_settings_override()
        
    def _exit_settings_override(self):
        self._settings_ctx_manager.__exit__(None, None, None)
