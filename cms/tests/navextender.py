# -*- coding: utf-8 -*-
from cms.models import Page
from cms.tests.base import CMSTestCase
from cms.tests.util.menu_extender import TestMenu
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Template
from menus.menu_pool import menu_pool

class NavExtenderTestCase(CMSTestCase):

    def setUp(self):
        
        settings.CMS_MODERATOR = False
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)
        menu_pool.clear(settings.SITE_ID)
        
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'CMSMenu':self.old_menu['CMSMenu'], 'TestMenu':TestMenu()}
      
    def tearDown(self):
        menu_pool.menus = self.old_menu
        
    def create_some_nodes(self):
        self.page1 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page2 = self.create_page(parent_page=self.page1, published=True, in_navigation=True)
        self.page3 = self.create_page(parent_page=self.page2, published=True, in_navigation=True)
        self.page4 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page5 = self.create_page(parent_page=self.page4, published=True, in_navigation=True)
        
    def test_01_menu_registration(self):
        self.assertEqual(len(menu_pool.menus), 2)
        self.assertEqual(len(menu_pool.modifiers) >=4, True)
        
    def test_02_extenders_on_root(self):
        self.create_some_nodes()
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.navigation_extenders = "TestMenu"
        page1.save()
        context = self.get_context()
        
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(len(nodes[0].children[3].children), 1)
        page1.in_navigation = False
        page1.save()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 5)
        
    def test_03_extenders_on_root_child(self):
        self.create_some_nodes()
        page4 = Page.objects.get(pk=self.page4.pk)
        page4.navigation_extenders = "TestMenu"
        page4.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[1].children), 4)
        
    def test_04_extenders_on_child(self):
        self.create_some_nodes()
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.in_navigation = False
        page1.save()
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.navigation_extenders = "TestMenu"
        page2.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(nodes[0].children[1].get_absolute_url(), "/" )
        
    def test_05_incorrect_nav_extender_in_db(self):
        self.create_some_nodes()
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.navigation_extenders = "SomethingWrong"
        page2.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        
        