# -*- coding: utf-8 -*-
from cms.menu import CMSMenu
from cms.models import Page
from cms.tests.base import CMSTestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Template
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

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
        settings.CMS_MODERATOR = True
        
    def create_some_nodes(self):
        """
        Creates the following structure:
        
        + P1
        | + P2
        |   + P3
        + P4
        | + P5
        + P6 (not in menu)
          + P7
          + P8
          
        """
        self.page1 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page2 = self.create_page(parent_page=self.page1, published=True, in_navigation=True)
        self.page3 = self.create_page(parent_page=self.page2, published=True, in_navigation=True)
        self.page4 = self.create_page(parent_page=None, published=True, in_navigation=True)
        self.page5 = self.create_page(parent_page=self.page4, published=True, in_navigation=True)
        self.page6 = self.create_page(parent_page=None, published=True, in_navigation=False)
        self.page7 = self.create_page(parent_page=self.page6, published=True, in_navigation=True)
        self.page8 = self.create_page(parent_page=self.page6, published=True, in_navigation=True)
        self.all_pages = [self.page1, self.page2, self.page3, self.page4,
                          self.page5, self.page6, self.page7, self.page8]
        self.top_level_pages = [self.page1, self.page4]
        self.level1_pages = [self.page2, self.page5,self.page7,self.page8]
        self.level2_pages = [self.page3]
        
    def test_01_basic_cms_menu(self):
        self.assertEqual(len(menu_pool.menus), 1)
        response = self.client.get(self.get_pages_root())
        self.assertEquals(response.status_code, 200)
        request = self.get_request()
        
        # test the cms menu class
        menu = CMSMenu()
        nodes = menu.get_nodes(request)
        self.assertEqual(len(nodes), len(self.all_pages))
        
    def test_02_show_menu(self):
        
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].selected, True)
        self.assertEqual(nodes[0].sibling, False)
        self.assertEqual(nodes[0].descendant, False)
        self.assertEqual(nodes[0].children[0].descendant, True)
        self.assertEqual(nodes[0].children[0].children[0].descendant, True)
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(nodes[1].get_absolute_url(), self.page4.get_absolute_url())
        self.assertEqual(nodes[1].sibling, True)
        self.assertEqual(nodes[1].selected, False)
    
    def test_03_only_active_tree(self):
        context = self.get_context()
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes[1].children), 0)
        self.assertEqual(len(nodes[0].children), 1)
        self.assertEqual(len(nodes[0].children[0].children), 1)
        context = self.get_context(path=self.page4.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes[1].children), 1)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_04_only_one_active_level(self):
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 1 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes[1].children), 0)
        self.assertEqual(len(nodes[0].children), 1)
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
    def test_05_only_level_zero(self):
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_menu 0 0 0 0 %}")
        tpl.render(context) 
        nodes = context['children']
        for node in nodes:
            self.assertEqual(len(node.children), 0)
        
    
    def test_06_only_level_one(self):
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_menu 1 1 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), len(self.level1_pages))
        for node in nodes:
            self.assertEqual(len(node.children), 0)
        
    
    def test_07_only_level_one_active(self):
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_menu 1 1 0 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].descendant, True)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_08_level_zero_and_one(self):
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_menu 0 1 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            self.assertEqual(len(node.children), 1)
            
    def test_09_show_submenu(self):
        context = self.get_context()
        # test standard show_menu 
        tpl = Template("{% load menu_tags %}{% show_sub_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(nodes[0].descendant, True)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(nodes[0].children), 1)
        
        tpl = Template("{% load menu_tags %}{% show_sub_menu 1  %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_10_show_breadcrumb(self):
        context = self.get_context(path=self.page3.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 3)
        tpl = Template("{% load menu_tags %}{% show_breadcrumb 1 %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 2)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 1)
        tpl = Template("{% load menu_tags %}{% show_breadcrumb 1 %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 0)
        
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.in_navigation = False
        page1.save()
        page2 = Page.objects.get(pk=self.page2.pk)
        context = self.get_context(path=self.page2.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(isinstance(nodes[0], NavigationNode), True)
        self.assertEqual(nodes[1].get_absolute_url(), page2.get_absolute_url())
        
    def test_11_language_chooser(self):
        # test simple language chooser with default args 
        context = self.get_context(path=self.page3.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% language_chooser %}")
        tpl.render(context) 
        self.assertEqual(len(context['languages']), len(settings.CMS_SITE_LANGUAGES[settings.SITE_ID]))
        self.assertEqual(context['current_language'], settings.LANGUAGE_CODE)
        # try a different template and some different args
        tpl = Template("{% load menu_tags %}{% language_chooser 'menu/test_language_chooser.html' %}")
        tpl.render(context) 
        self.assertEqual(context['template'], 'menu/test_language_chooser.html')
        tpl = Template("{% load menu_tags %}{% language_chooser 'short' 'menu/test_language_chooser.html' %}")
        tpl.render(context) 
        self.assertEqual(context['template'], 'menu/test_language_chooser.html')
        for lang in context['languages']:
            self.assertEqual(*lang)
        
        
    def test_12_page_language_url(self):
        context = self.get_context(path=self.page3.get_absolute_url())
        tpl = Template("{%% load menu_tags %%}{%% page_language_url '%s' %%}" % settings.LANGUAGES[0][0])
        url = tpl.render(context)
        self.assertEqual( url, "/%s%s" % (settings.LANGUAGES[0][0], self.page3.get_absolute_url()))
        
    def test_13_show_menu_below_id(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.reverse_id = "hello"
        page2.save()
        page2 = Page.objects.get(pk=self.page2.pk)
        self.assertEqual(page2.reverse_id, "hello")
        context = self.get_context(path=self.page5.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'hello' %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), self.page3.get_absolute_url())
        page2.in_navigation = False
        page2.save()
        context = self.get_context(path=self.page5.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'hello' %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), self.page3.get_absolute_url())
        
        
    def test_14_unpublished(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.published = False
        page2.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
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
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), "%s%s/" % (self.get_pages_root(), self.page2.get_slug()))
        self.assertEqual(nodes[0].children[0].get_absolute_url(), "%s%s/%s/" % (self.get_pages_root(), self.page2.get_slug(), self.page3.get_slug()))
        page4 = Page.objects.get(pk=self.page4.pk)
        page4.in_navigation = True
        page4.save()
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        
    def test_16_empty_menu(self):
        Page.objects.all().delete()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 0)
        
    def test_17_softroot(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        page2.soft_root = True
        page2.save()
        context = self.get_context(path=page2.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page2.get_absolute_url())
        page3 = Page.objects.get(pk=self.page3.pk)
        context = self.get_context(path=page3.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page2.get_absolute_url())
        
        page1 = Page.objects.get(pk=self.page1.pk)
        context = self.get_context(path=page1.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
        context = self.get_context(path="/no/real/path/")
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
        page5 = Page.objects.get(pk=self.page5.pk)
        context = self.get_context(path=page5.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
    def test_18_show_submenu_from_non_menu_page(self):
        """
        Here's the structure bit we're interested in:
        
        + P6 (not in menu)
          + P7
          + P8
          
        When we render P6, there should be a menu entry for P7 and P8 if the
        tag parameters are "1 XXX XXX XXX"
        """
        page6 = Page.objects.get(pk=self.page6.pk)
        context = self.get_context(page6.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 1 100 0 1 %}")
        tpl.render(context) 
        nodes = context['children']
        number_of_p6_children = len(page6.children.filter(in_navigation=True))
        self.assertEqual(len(nodes), number_of_p6_children)
        
        page7 = Page.objects.get(pk=self.page7.pk)
        context = self.get_context(page7.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 1 100 0 1 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), number_of_p6_children)
        
        tpl = Template("{% load menu_tags %}{% show_menu 2 100 0 1 %}")
        tpl.render(context) 
        nodes = context['children']
        number_of_p7_children = len(page7.children.filter(in_navigation=True))
        self.assertEqual(len(nodes), number_of_p7_children)
        
    def test_19_show_breadcrumb_invisible(self):
        invisible_page = self.create_page(parent_page=self.page3, 
                                          published=True, 
                                          in_navigation=False)
        context = self.get_context(path=invisible_page.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 3)
        tpl = Template("{% load menu_tags %}{% show_breadcrumb 'menu/breadcrumb.html' 1 %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 3)
        tpl = Template("{% load menu_tags %}{% show_breadcrumb 'menu/breadcrumb.html' 0 %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 4)

    def test_20_build_nodes_inner_for_worst_case_menu(self):
        '''
            Tests the worst case scenario
            
            node5
             node4
              node3
               node2
                node1
        '''
        node1 = NavigationNode('Test1', '/test1/', 1, 2)
        node2 = NavigationNode('Test2', '/test2/', 2, 3)
        node3 = NavigationNode('Test3', '/test3/', 3, 4)
        node4 = NavigationNode('Test4', '/test4/', 4, 5)
        node5 = NavigationNode('Test5', '/test5/', 5, None)
        
        menu_class_name = 'Test'
        nodes = [node1,node2,node3,node4,node5,]
        len_nodes = len(nodes)
        
        final_list = menu_pool._build_nodes_inner_for_one_menu(nodes, 
                                                               menu_class_name)
        self.assertEqual(len(final_list), len_nodes)
        
        self.assertEqual(node1.parent, node2)
        self.assertEqual(node2.parent, node3)
        self.assertEqual(node3.parent, node4)
        self.assertEqual(node4.parent, node5)
        self.assertEqual(node5.parent, None)
        
        self.assertEqual(node1.children, [])
        self.assertEqual(node2.children, [node1])
        self.assertEqual(node3.children, [node2])
        self.assertEqual(node4.children, [node3])
        self.assertEqual(node5.children, [node4])
        
    def test_21_build_nodes_inner_for_circular_menu(self):
        '''
        TODO: 
            To properly handle this test we need to have a circular dependency 
            detection system.
            Go nuts implementing it :)
        '''
        pass
    
    def test_22_build_nodes_inner_for_broken_menu(self):
        '''
            Tests a broken menu tree (non-existing parent)
            
            node5
             node4
              node3
              
            <non-existant>
             node2
              node1
        '''
        node1 = NavigationNode('Test1', '/test1/', 1, 2)
        node2 = NavigationNode('Test2', '/test2/', 2, 12)
        node3 = NavigationNode('Test3', '/test3/', 3, 4)
        node4 = NavigationNode('Test4', '/test4/', 4, 5)
        node5 = NavigationNode('Test5', '/test5/', 5, None)
        
        menu_class_name = 'Test'
        nodes = [node1,node2,node3,node4,node5,]
        
        final_list = menu_pool._build_nodes_inner_for_one_menu(nodes, 
                                                               menu_class_name)
        self.assertEqual(len(final_list), 3) 
        self.assertFalse(node1 in final_list)
        self.assertFalse(node2 in final_list)
        
        self.assertEqual(node1.parent, None)
        self.assertEqual(node2.parent, None)
        self.assertEqual(node3.parent, node4)
        self.assertEqual(node4.parent, node5)
        self.assertEqual(node5.parent, None)
        
        self.assertEqual(node1.children, [])
        self.assertEqual(node2.children, [])
        self.assertEqual(node3.children, [])
        self.assertEqual(node4.children, [node3])
        self.assertEqual(node5.children, [node4])
