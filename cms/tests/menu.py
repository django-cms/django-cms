# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase
from cms.models import Page
from cms.menu import CMSMenu
from menus.templatetags.menu_tags import show_menu, show_sub_menu,\
    show_breadcrumb, language_chooser, page_language_url, show_menu_below_id
from menus.menu_pool import menu_pool
from menus.base import NavigationNode


class MenusTestCase(CMSTestCase):

    def setUp(self):
        settings.CMS_MODERATOR = False
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'CMSMenu':self.old_menu['CMSMenu']}
        menu_pool.clear(settings.SITE_ID)
        self.create_some_nodes()
        
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
        response = self.client.get("/")
        self.assertEquals(response.status_code, 200)
        request = self.get_request()
        
        # test the cms menu class
        menu = CMSMenu()
        nodes = menu.get_nodes(request)
        self.assertEqual(len(nodes), 5)
        
    def test_02_show_menu(self):
        
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
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 100, 0, 1)['children']
        self.assertEqual(len(nodes[1].children), 0)
        self.assertEqual(len(nodes[0].children), 1)
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
    def test_05_only_level_zero(self):
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 0, 0, 0)['children']
        for node in nodes:
            self.assertEqual(len(node.children), 0)
        
    
    def test_06_only_level_one(self):
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 1, 1, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            self.assertEqual(len(node.children), 0)
        
    
    def test_07_only_level_one_active(self):
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 1, 1, 0, 100)['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].descendant, True)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_08_level_zero_and_one(self):
        context = self.get_context()
        # test standard show_menu 
        nodes = show_menu(context, 0, 1, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            self.assertEqual(len(node.children), 1)
            
    def test_09_show_submenu(self):
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
        
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.in_navigation = False
        page1.save()
        page2 = Page.objects.get(pk=self.page2.pk)
        context = self.get_context(path=self.page2.get_absolute_url())
        nodes = show_breadcrumb(context)['ancestors']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), "/")
        self.assertEqual(isinstance(nodes[0], NavigationNode), True)
        self.assertEqual(nodes[1].get_absolute_url(), page2.get_absolute_url())
        
    def test_11_language_chooser(self):
        context = self.get_context(path=self.page3.get_absolute_url())
        new_context = language_chooser(context)
        self.assertEqual(len(new_context['languages']), len(settings.LANGUAGES))
        self.assertEqual(new_context['current_language'], settings.LANGUAGES[0][0])
        
    def test_12_page_language_url(self):
        context = self.get_context(path=self.page3.get_absolute_url())
        url = page_language_url(context, settings.LANGUAGES[0][0])['content']
        self.assertEqual( url, "/%s%s" % (settings.LANGUAGES[0][0], self.page3.get_absolute_url()))
        
    def test_13_show_menu_below_id(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.reverse_id = "hello"
        page2.save()
        page2 = Page.objects.get(pk=self.page2.pk)
        self.assertEqual(page2.reverse_id, "hello")
        context = self.get_context(path=self.page5.get_absolute_url())
        nodes = show_menu_below_id(context, "hello")['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), self.page3.get_absolute_url())
        page2.in_navigation = False
        page2.save()
        context = self.get_context(path=self.page5.get_absolute_url())
        nodes = show_menu_below_id(context, "hello")['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), self.page3.get_absolute_url())
        
        
    def test_14_unpublished(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.published = False
        page2.save()
        context = self.get_context()
        nodes = show_menu(context)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_15_home_not_in_menu(self):
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.in_navigation = False
        page1.save()
        page4 = Page.objects.get(pk=self.page4.pk)
        page4.in_navigation = False
        page4.save()
        context = self.get_context()
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), "/%s/" % self.page2.get_slug())
        self.assertEqual(nodes[0].children[0].get_absolute_url(), "/%s/%s/" % (self.page2.get_slug(), self.page3.get_slug()))
        page4 = Page.objects.get(pk=self.page4.pk)
        page4.in_navigation = True
        page4.save()
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        
    def test_15_empty_menu(self):
        Page.objects.all().delete()
        request = self.get_request()
        nodes = menu_pool.get_nodes(request)
        context = self.get_context()
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        
    def test_16_softroot(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.soft_root = True
        page2.save()
        context = self.get_context(path=page2.get_absolute_url())
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page2.get_absolute_url())
        page3 = Page.objects.get(pk=self.page3.pk)
        context = self.get_context(path=page3.get_absolute_url())
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page2.get_absolute_url())
        
        page1 = Page.objects.get(pk=self.page1.pk)
        context = self.get_context(path=page1.get_absolute_url())
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
        context = self.get_context(path="/no/real/path/")
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
        page5 = Page.objects.get(pk=self.page5.pk)
        context = self.get_context(path=page5.get_absolute_url())
        nodes = show_menu(context, 0, 100, 100, 100)['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        