# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from cms.models import Page
from menus.templatetags.menu_tags import show_menu
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from django.conf import settings
from cms.tests.base import CMSTestCase
from cms.menu import CMSMenu
from menus.menu_pool import menu_pool
from cms.tests.util.menu_extender import TestMenu

class NavExtenderTestCase(CMSTestCase):

    def setUp(self):
        
        settings.CMS_MODERATOR = False
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)
        menu_pool.menus['TestMenu'] = TestMenu()
        
    def tearDown(self):
        del menu_pool.menus['TestMenu']
        
    def create_some_nodes(self):
        self.page1 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page2 = self.create_page(parent_page=self.page1, published=True, in_navigation=True)
        self.page3 = self.create_page(parent_page=self.page2, published=True, in_navigation=True)
        self.page4 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page5 = self.create_page(parent_page=self.page4, published=True, in_navigation=True)
        
    def test_01_menu_registration(self):
        self.assertEqual(len(menu_pool.menus) >= 2, True)
        
    def test_02_extenders_on_root(self):
        menu_pool.clear()
        self.create_some_nodes()
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.navigation_extenders = "TestMenu"
        page1.save()
        context = self.get_context()
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(len(nodes[0].children[3].children), 1)
        page1.in_navigation = False
        page1.save()
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 6)
        
    def test_03_extenders_on_root_child(self):
        menu_pool.clear()
        self.create_some_nodes()
        page4 = Page.objects.get(pk=self.page4.pk)
        page4.navigation_extenders = "TestMenu"
        page4.save()
        context = self.get_context()
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[1].children), 4)
        
    def test_04_extenders_on_child(self):
        menu_pool.clear()
        self.create_some_nodes()
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.navigation_extenders = "TestMenu"
        page2.save()
        context = self.get_context()
        nodes = show_menu(context)['children']
        self.assertEqual(nodes, 2)
        self.assertEqual(nodes[0].children, 5)
        