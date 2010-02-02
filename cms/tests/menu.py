# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase
from cms.models import Page
from cms.menu import CMSMenu
from menus.templatetags.menu_tags import show_menu, show_sub_menu,\
    show_breadcrumb, language_chooser, page_language_url, show_menu_below_id
from menus.menu_pool import menu_pool


class MenusTestCase(CMSTestCase):

    def setUp(self):
        settings.CMS_MODERATOR = False
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'CMSMenu':self.old_menu['CMSMenu']}
        
    def tearDown(self):
        menu_pool.menus = self.old_menu
        
    def create_some_nodes(self):
        self.page1 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page2 = self.create_page(parent_page=self.page1, published=True, in_navigation=True)
        self.page3 = self.create_page(parent_page=self.page2, published=True, in_navigation=True)
        self.page4 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page5 = self.create_page(parent_page=self.page4, published=True, in_navigation=True)
        
    def test_01_basic_cms_menu(self):
        self.assertEqual(len(menu_pool.menus), 1)
        self.create_some_nodes()
        response = self.client.get("/")
        self.assertEquals(response.status_code, 200)
        request = self.get_request()
        
        # test the cms menu class
        menu = CMSMenu()
        nodes = menu.get_nodes(request)
        self.assertEqual(len(nodes), 5)
        
    def test_02_show_menu(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].selected, True)
        self.assertEqual(nodes[0].sibling, False)
        self.assertEqual(nodes[0].descendant, False)
        self.assertEqual(nodes[0].children[0].descendant, True)
        self.assertEqual(nodes[0].children[0].children[0].descendant, True)
        self.assertEqual(nodes[0].get_absolute_url(), "/")
        self.assertEqual(nodes[1].get_absolute_url(), self.page4.get_absolute_url())
        self.assertEqual(nodes[1].sibling, True)
        self.assertEqual(nodes[1].selected, False)
    
    def test_03_only_active_tree(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 100, 0, 100)['children']
        self.assertEqual(len(nodes[1].children), 0)
        self.assertEqual(len(nodes[0].children), 1)
        self.assertEqual(len(nodes[0].children[0].children), 1)
        context = self.get_context(path=self.page4.get_absolute_url())
        nodes = show_menu(context, 0, 100, 0, 100)['children']
        self.assertEqual(len(nodes[1].children), 1)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_04_only_one_active_level(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 100, 0, 1)['children']
        self.assertEqual(len(nodes[1].children), 0)
        self.assertEqual(len(nodes[0].children), 1)
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
    def test_05_only_level_zero(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 0, 0, 0)['children']
        for node in nodes:
            self.assertEqual(len(node.children), 0)
        
    
    def test_06_only_level_one(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 1, 1, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            self.assertEqual(len(node.children), 0)
        
    
    def test_07_only_level_one_active(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 1, 1, 0, 100)['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].descendant, True)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_08_level_zero_and_one(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 1, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            self.assertEqual(len(node.children), 1)
            
    def test_09_show_submenu(self):
        self.create_some_nodes()
        context = self.get_context()
        # test standard show_menu 
        nodes = show_sub_menu(context)['children']
        self.assertEqual(nodes[0].descendant, True)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(nodes[0].children), 1)
        
        nodes = show_sub_menu(context, 1)['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_10_show_breadcrumb(self):
        self.create_some_nodes()
        context = self.get_context(path=self.page3.get_absolute_url())
        nodes = show_breadcrumb(context)['ancestors']
        self.assertEqual(len(nodes), 3)
        nodes = show_breadcrumb(context, 1)['ancestors']
        self.assertEqual(len(nodes), 2)
        context = self.get_context()
        nodes = show_breadcrumb(context)['ancestors']
        self.assertEqual(len(nodes), 1)
        nodes = show_breadcrumb(context, 1)['ancestors']
        self.assertEqual(len(nodes), 0)
        
    def test_11_language_chooser(self):
        self.create_some_nodes()
        context = self.get_context(path=self.page3.get_absolute_url())
        new_context = language_chooser(context)
        self.assertEqual(len(new_context['languages']), len(settings.LANGUAGES))
        self.assertEqual(new_context['current_language'], settings.LANGUAGES[0][0])
        
    def test_12_page_language_url(self):
        self.create_some_nodes()
        context = self.get_context(path=self.page3.get_absolute_url())
        url = page_language_url(context, settings.LANGUAGES[0][0])['content']
        self.assertEqual( url, "/%s%s" % (settings.LANGUAGES[0][0], self.page3.get_absolute_url()))
        
    def test_13_show_menu_below_id(self):
        menu_pool.clear()
        self.create_some_nodes()
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.reverse_id = "hello"
        page2.save()
        page2 = Page.objects.get(pk=self.page2.pk)
        self.assertEqual(page2.reverse_id, "hello")
        context = self.get_context(path=self.page5.get_absolute_url())
        nodes = show_menu_below_id(context, "hello")['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), self.page3.get_absolute_url())
        
        
    def test_14_unpublished(self):
        menu_pool.clear()
        self.create_some_nodes()
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.published = False
        page2.save()
        context = self.get_context()
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_15_home_not_in_menu(self):
        menu_pool.clear()
        self.create_some_nodes()
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.in_navigation = False
        page1.save()
        context = self.get_context()
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), "/%s/" % self.page2.get_slug())
        