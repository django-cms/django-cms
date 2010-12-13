# -*- coding: utf-8 -*-
from cms.models import Page
from cms.tests.base import CMSTestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Template
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

class NonRootCase(CMSTestCase):
    urls = 'testapp.nonroot_urls'

    def setUp(self):
        settings.CMS_MODERATOR = False
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)

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
        | + P5

        """
        self.page1 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page2 = self.create_page(parent_page=self.page1, published=True, in_navigation=True)
        self.page3 = self.create_page(parent_page=self.page2, published=True, in_navigation=True)
        self.page4 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.all_pages = [self.page1, self.page2, self.page3, self.page4]
        self.top_level_pages = [self.page1, self.page4]
        self.level1_pages = [self.page2]
        self.level2_pages = [self.page3]
        

    def test_01_basic_cms_menu(self):
        response = self.client.get(self.get_pages_root())
        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.get_pages_root(), "/content/")

    def test_02_show_menu(self):
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(nodes[0].get_absolute_url(), "/content/")

    def test_03_show_breadcrumb(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        context = self.get_context(path=self.page2.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(nodes[0].get_absolute_url(), "/content/")
        self.assertEqual(isinstance(nodes[0], NavigationNode), True)
        self.assertEqual(nodes[1].get_absolute_url(), page2.get_absolute_url())
