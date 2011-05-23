from __future__ import with_statement
from cms.api import (_generate_valid_slug, create_page, _verify_plugin_type, 
    assign_user_to_page, publish_page)
from cms.apphook_pool import apphook_pool
from cms.models.pagemodel import Page
from cms.plugin_base import CMSPluginBase
from cms.plugins.text.cms_plugins import TextPlugin
from cms.plugins.text.models import Text
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.menu_extender import TestMenu
from cms.test_utils.util.mock import AttributeObject
from cms.tests.apphooks import APP_MODULE, APP_NAME
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test.testcases import TestCase
from menus.menu_pool import menu_pool
import sys


def _grant_page_permission(user, codename):
    content_type = ContentType.objects.get_by_natural_key('cms', 'page')
    perm = Permission.objects.get_or_create(codename='%s_page' % codename,
                                            content_type=content_type)[0]
    user.user_permissions.add(perm)

class PythonAPITests(TestCase):
    def _get_default_create_page_arguments(self):
        return {
            'title': 'Test',
            'template': 'nav_playground.html',
            'language': 'en'
        }
        
    def test_generate_valid_slug(self):
        title = "Hello Title"
        expected_slug = "hello-title"
        # empty db, it should just slugify
        slug = _generate_valid_slug(title, None, 'en')
        self.assertEqual(slug, expected_slug)
        
    def test_generage_valid_slug_check_existing(self):
        title = "Hello Title"
        create_page(title, 'nav_playground.html', 'en')
        # second time with same title, it should append -1
        expected_slug = "hello-title-1"
        slug = _generate_valid_slug(title, None, 'en')
        self.assertEqual(slug, expected_slug)
        
    def test_generage_valid_slug_check_parent(self):
        title = "Hello Title"
        page = create_page(title, 'nav_playground.html', 'en')
        # second time with same title, it should append -1
        expected_slug = "hello-title"
        slug = _generate_valid_slug(title, page, 'en')
        self.assertEqual(slug, expected_slug)
        
    def test_generage_valid_slug_check_parent_existing(self):
        title = "Hello Title"
        page = create_page(title, 'nav_playground.html', 'en')
        create_page(title, 'nav_playground.html', 'en', parent=page)
        # second time with same title, it should append -1
        expected_slug = "hello-title-1"
        slug = _generate_valid_slug(title, page, 'en')
        self.assertEqual(slug, expected_slug)
    
    def test_invalid_apphook_type(self):
        self.assertRaises(TypeError, create_page, apphook=1,
                          **self._get_default_create_page_arguments())
    
    def test_apphook_by_class(self):
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        apphooks = (
            '%s.%s' % (APP_MODULE, APP_NAME),
        )
        
        with SettingsOverride(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            apphook = apphook_pool.get_apphook(APP_NAME)
            page = create_page(apphook=apphook,
                               **self._get_default_create_page_arguments())
            self.assertEqual(page.get_application_urls('en'), APP_NAME)
    
    def test_invalid_dates(self):
        self.assertRaises(AssertionError, create_page, publication_date=1,
                          **self._get_default_create_page_arguments())
        self.assertRaises(AssertionError, create_page, publication_end_date=1,
                          **self._get_default_create_page_arguments())
        
    def test_nav_extenders_invalid_type(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'TestMenu':TestMenu()}
        self.assertRaises(AssertionError, create_page, navigation_extenders=1,
                          **self._get_default_create_page_arguments())
        menu_pool.menus = self.old_menu
        
    def test_nav_extenders_invalid_menu(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {}
        self.assertRaises(AssertionError, create_page,
                          navigation_extenders=TestMenu,
                          **self._get_default_create_page_arguments())
        menu_pool.menus = self.old_menu
        
    def test_nav_extenders_valid(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'TestMenu':TestMenu()}
        page = create_page(navigation_extenders='TestMenu',
                           **self._get_default_create_page_arguments())
        self.assertEqual(page.navigation_extenders, 'TestMenu')
        menu_pool.menus = self.old_menu
    
    def test_verify_plugin_type_invalid_type(self):
        self.assertRaises(TypeError, _verify_plugin_type, 1)
    
    def test_verify_plugin_type_string(self):
        plugin_model, plugin_type = _verify_plugin_type("TextPlugin")
        self.assertEqual(plugin_model, Text)
        self.assertEqual(plugin_type, 'TextPlugin')
        
    def test_verify_plugin_type_string_invalid(self):
        self.assertRaises(TypeError, _verify_plugin_type, "InvalidPlugin")
    
    def test_verify_plugin_type_plugin_class(self):
        plugin_model, plugin_type = _verify_plugin_type(TextPlugin)
        self.assertEqual(plugin_model, Text)
        self.assertEqual(plugin_type, 'TextPlugin')
    
    def test_verify_plugin_type_invalid_plugin_class(self):
        class InvalidPlugin(CMSPluginBase):
            model = Text
        self.assertRaises(AssertionError, _verify_plugin_type, InvalidPlugin)
    
    def test_assign_user_to_page_nothing(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = User.objects.create(username='user', email='user@django-cms.org',
                                   is_staff=True, is_active=True)
        request = AttributeObject(user=user)
        self.assertFalse(page.has_change_permission(request))
    
    def test_assign_user_to_page_single(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = User.objects.create(username='user', email='user@django-cms.org',
                                   is_staff=True, is_active=True)
        request = AttributeObject(user=user)
        assign_user_to_page(page, user, can_change=True)
        self.assertFalse(page.has_change_permission(request))
        self.assertFalse(page.has_add_permission(request))
        _grant_page_permission(user, 'change')
        page = Page.objects.get(pk=page.pk)
        user = User.objects.get(pk=user.pk)
        request = AttributeObject(user=user)
        self.assertTrue(page.has_change_permission(request))
        self.assertFalse(page.has_add_permission(request))
    
    def test_assign_user_to_page_all(self):
        page = create_page(**self._get_default_create_page_arguments())
        user = User.objects.create(username='user', email='user@django-cms.org',
                                   is_staff=True, is_active=True)
        request = AttributeObject(user=user)
        assign_user_to_page(page, user, grant_all=True)
        self.assertFalse(page.has_change_permission(request))
        self.assertTrue(page.has_add_permission(request))
        _grant_page_permission(user, 'change')
        _grant_page_permission(user, 'add')
        page = Page.objects.get(pk=page.pk)
        user = User.objects.get(pk=user.pk)
        request = AttributeObject(user=user)
        self.assertTrue(page.has_change_permission(request))
        self.assertTrue(page.has_add_permission(request))

    def test_page_overwrite_url_default(self):
        page = create_page(**self._get_default_create_page_arguments())
        self.assertFalse(page.get_title_obj_attribute('has_url_overwrite'))
        self.assertEqual(page.get_title_obj_attribute('path'), 'test')

    def test_create_page_can_overwrite_url(self):
        page_attrs = self._get_default_create_page_arguments()
        page_attrs["overwrite_url"] = 'test/home'
        page = create_page(**page_attrs)
        self.assertTrue(page.get_title_obj_attribute('has_url_overwrite'))
        self.assertEqual(page.get_title_obj_attribute('path'), 'test/home')
