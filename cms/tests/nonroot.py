# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.template import Template
from menus.base import NavigationNode


class NonRootCase(CMSTestCase):
    urls = 'project.nonroot_urls'

    def setUp(self):
        with SettingsOverride(CMS_MODERATOR = False):
            u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
            u.set_password("test")
            u.save()
            with self.login_user_context(u):
                self.create_some_pages()
        
    # def tearDown(self):
    #     menu_pool.menus = self.old_menu

    def create_some_pages(self):
        """
        Creates the following structure:
        
        + P1
        | + P2
        |   + P3
        + P4

        """
        self.page1 = create_page("page1", "nav_playground.html", "en",
                                 published=True, in_navigation=True)
        self.page2 = create_page("page2", "nav_playground.html", "en",
                          parent=self.page1, published=True, in_navigation=True)
        self.page3 = create_page("page3", "nav_playground.html", "en",
                          parent=self.page2, published=True, in_navigation=True)
        self.page4 = create_page("page4", "nav_playground.html", "en",
                                      published=True, in_navigation=True)
        self.all_pages = [self.page1, self.page2, self.page3, self.page4]
        self.top_level_pages = [self.page1, self.page4]
        self.level1_pages = [self.page2]
        self.level2_pages = [self.page3]
        

    def test_basic_cms_menu(self):
        with SettingsOverride(CMS_MODERATOR = False):
            response = self.client.get(self.get_pages_root())
            self.assertEquals(response.status_code, 200)
            self.assertEquals(self.get_pages_root(), "/content/")

    def test_show_menu(self):
        with SettingsOverride(CMS_MODERATOR = False):
            context = self.get_context()
            tpl = Template("{% load menu_tags %}{% show_menu %}")
            tpl.render(context) 
            nodes = context['children']
            self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
            self.assertEqual(nodes[0].get_absolute_url(), "/content/")

    def test_show_breadcrumb(self):
        with SettingsOverride(CMS_MODERATOR = False):    
            page2 = Page.objects.get(pk=self.page2.pk)
            context = self.get_context(path=self.page2.get_absolute_url())
            tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
            tpl.render(context) 
            nodes = context['ancestors']
            self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
            self.assertEqual(nodes[0].get_absolute_url(), "/content/")
            self.assertEqual(isinstance(nodes[0], NavigationNode), True)
            self.assertEqual(nodes[1].get_absolute_url(), page2.get_absolute_url())
