# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.models import Page
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.menu_extender import TestMenu
from django.conf import settings
from django.template import Template
from menus.menu_pool import menu_pool

class NavExtenderTestCase(SettingsOverrideTestCase):
    settings_overrides = {'CMS_MODERATOR': False}
    fixtures = ['navextenders']
    
    """
    Tree from fixture:
    
        page1
            page2
                page3
        page4
            page5
    """
    
    def setUp(self):
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'CMSMenu':self.old_menu['CMSMenu'], 'TestMenu':TestMenu()}
          
    def tearDown(self):
        menu_pool.menus = self.old_menu
        
    def test_menu_registration(self):
        self.assertEqual(len(menu_pool.menus), 2)
        self.assertEqual(len(menu_pool.modifiers) >=4, True)
        
    def test_extenders_on_root(self):
        Page.objects.filter(pk=1).update(navigation_extenders="TestMenu")
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(len(nodes[0].children[3].children), 1)
        Page.objects.filter(pk=1).update(in_navigation=False)
        menu_pool.clear(settings.SITE_ID)
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 5)
        
    def test_extenders_on_root_child(self):
        Page.objects.filter(pk=4).update(navigation_extenders="TestMenu")
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[1].children), 4)
        
    def test_extenders_on_child(self):
        """
        TestMenu has 4 flat nodes
        """
        Page.objects.filter(pk=1).update(in_navigation=False)
        Page.objects.filter(pk=2).update(navigation_extenders="TestMenu")
        menu_pool.clear(settings.SITE_ID)
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(nodes[0].children[1].get_absolute_url(), "/" )
        
    def test_incorrect_nav_extender_in_db(self):
        Page.objects.filter(pk=2).update(navigation_extenders="SomethingWrong")
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)