# -*- coding: utf-8 -*-
from cms.models import Page
from cms.test_utils.util.context_managers import (UserLoginContext, 
    SettingsOverride, _AssertNumQueriesContext)
from cms.test_utils.util.request_factory import RequestFactory
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS
from django.template.context import Context
from django.test import testcases
from django.test.client import Client
from menus.menu_pool import menu_pool
from urlparse import urljoin
import sys
import urllib
import warnings



URL_CMS_PAGE = "/en/admin/cms/page/"
URL_CMS_PAGE_ADD = urljoin(URL_CMS_PAGE, "add/")
URL_CMS_PAGE_CHANGE = urljoin(URL_CMS_PAGE, "%d/")
URL_CMS_PAGE_DELETE = urljoin(URL_CMS_PAGE_CHANGE, "delete/")
URL_CMS_PLUGIN_ADD = urljoin(URL_CMS_PAGE_CHANGE, "add-plugin/")
URL_CMS_PLUGIN_EDIT = urljoin(URL_CMS_PAGE_CHANGE, "edit-plugin/")
URL_CMS_PLUGIN_REMOVE = urljoin(URL_CMS_PAGE_CHANGE, "remove-plugin/")
URL_CMS_TRANSLATION_DELETE = urljoin(URL_CMS_PAGE_CHANGE, "delete-translation/")

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
    
    
if hasattr(testcases.TestCase, 'assertNumQueries'):
    TestCase = testcases.TestCase
else:
    class TestCase(testcases.TestCase):
        def assertNumQueries(self, num, func=None, *args, **kwargs):
            if hasattr(testcases.TestCase, 'assertNumQueries'):
                return super(TestCase, self).assertNumQueries(num, func, *args, **kwargs)
            return self._assertNumQueries(num, func, *args, **kwargs)
    
        def _assertNumQueries(self, num, func=None, *args, **kwargs):
            """
            Backport from Django 1.3 for Django 1.2
            """
            using = kwargs.pop("using", DEFAULT_DB_ALIAS)
            connection = connections[using]
    
            context = _AssertNumQueriesContext(self, num, connection)
            if func is None:
                return context
    
            # Basically emulate the `with` statement here.
    
            context.__enter__()
            try:
                func(*args, **kwargs)
            except:
                context.__exit__(*sys.exc_info())
                raise
            else:
                context.__exit__(*sys.exc_info())
                
class CMSTestCase(TestCase):
    counter = 1
    
    def _fixture_setup(self):
        super(CMSTestCase, self)._fixture_setup()
        self.create_fixtures()
        self.client = Client()
    
    def create_fixtures(self):
        pass
            
    def _post_teardown(self):
        # Needed to clean the menu keys cache, see menu.menu_pool.clear()
        menu_pool.clear()
        super(CMSTestCase, self)._post_teardown()
        
    def login_user_context(self, user):
        return UserLoginContext(self, user)
        
    def get_superuser(self):
        try:
            admin = User.objects.get(username="admin")
        except User.DoesNotExist:
            admin = User(username="admin", is_staff=True, is_active=True, is_superuser=True)
            admin.set_password("admin")
            admin.save()
        return admin
        
    def get_staff_user_with_no_permissions(self):
        """
        Used in security tests
        """
        staff = User(username="staff", is_staff=True, is_active=True)
        staff.set_password("staff")
        staff.save()
        return staff
    
    def get_new_page_data(self, parent_id=''):
        page_data = {
            'title': 'test page %d' % self.counter,
            'slug': 'test-page-%d' % self.counter,
            'language': settings.LANGUAGES[0][0],
            'template': 'nav_playground.html',
            'parent': parent_id,
            'site': 1,
        }
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        page_data['pagepermission_set-2-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-2-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-2-MAX_NUM_FORMS'] = 0
        
        self.counter = self.counter + 1
        return page_data
    
    def print_page_structure(self, qs):
        """Just a helper to see the page struct.
        """
        for page in qs.order_by('tree_id', 'lft'):
            ident = "  " * page.level
            
            print "%s%s (%s), lft: %s, rght: %s, tree_id: %s" % (ident, page,
                                    page.pk, page.lft, page.rght, page.tree_id)
    
    def print_node_structure(self, nodes, *extra):
        def _rec(nodes, level=0):
            ident = level * '  '
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
        
    def get_request(self, path=None, language=None, post_data=None, enforce_csrf_checks=False):
        factory = RequestFactory()
        
        if not path:
            path = self.get_pages_root()
        
        if not language:
            language = settings.LANGUAGES[0][0]
        
        if post_data:
            request = factory.post(path, post_data)
        else:
            request = factory.get(path)
        request.session = self.client.session
        request.user = getattr(self, 'user', AnonymousUser())
        request.LANGUAGE_CODE = language
        request._dont_enforce_csrf_checks = not enforce_csrf_checks
        return request
    
    def check_published_page_attributes(self, page):
        public_page = page.publisher_public
        
        if page.parent:
            self.assertEqual(page.parent_id, public_page.parent.publisher_draft.id)
        
        self.assertEqual(page.level, public_page.level)
        
        # TODO: add check for siblings
        draft_siblings = list(page.get_siblings(True).filter(
                publisher_is_draft=True
            ).order_by('tree_id', 'parent', 'lft'))
        public_siblings = list(public_page.get_siblings(True).filter(
                publisher_is_draft=False
            ).order_by('tree_id', 'parent', 'lft'))
        skip = 0
        for i, sibling in enumerate(draft_siblings):
            if not sibling.publisher_public_id:
                skip += 1
                continue
            self.assertEqual(sibling.id,
                public_siblings[i-skip].publisher_draft.id)
    
    def request_moderation(self, page, level):
        """Assign current logged in user to the moderators / change moderation
        
        Args:
            page: Page on which moderation should be changed
        
            level <0, 7>: Level of moderation, 
                1 - moderate page
                2 - moderate children
                4 - moderate descendants
                + combinations
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
