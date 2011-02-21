# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.menu import CMSMenu
from cms.models import Page
from cms.test.testcases import SettingsOverrideTestCase
from cms.test.util.mock import AttributeObject
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Template
from menus.base import NavigationNode
from menus.menu_pool import menu_pool, _build_nodes_inner_for_one_menu
from menus.utils import mark_descendants, find_selected, cut_levels


class BaseMenuTest(SettingsOverrideTestCase):
    settings_overrides = {
        'CMS_MODERATOR': False
    }
    
    def _get_nodes(self, path='/'):
        node1 = NavigationNode('1', '/1/', 1)
        node2 = NavigationNode('2', '/2/', 2, 1)
        node3 = NavigationNode('3', '/3/', 3, 2)
        node4 = NavigationNode('4', '/4/', 4, 2)
        node5 = NavigationNode('5', '/5/', 5)
        nodes = [node1, node2, node3, node4, node5]
        tree = _build_nodes_inner_for_one_menu([n for n in nodes], "test")
        request = self.get_request(path)
        menu_pool.apply_modifiers(tree, request)
        return tree, nodes

    def setUp(self):
        super(BaseMenuTest, self).setUp()
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        self.login_user(u)
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'CMSMenu':self.old_menu['CMSMenu']}
        menu_pool.clear(settings.SITE_ID)
        
    def tearDown(self):
        menu_pool.menus = self.old_menu
        super(BaseMenuTest, self).tearDown()


class FixturesMenuTests(BaseMenuTest):
    """
    Tree from fixture:
        
        + P1
        | + P2
        |   + P3
        + P4
        | + P5
        + P6 (not in menu)
          + P7
          + P8
    """
    fixtures = ['menus.json']
    
    def get_page(self, num):
        return Page.objects.get(pk=num)
    
    def get_level(self, num):
        return Page.objects.filter(level=num)
    
    def get_all_pages(self):
        return Page.objects.all()
    
    def test_01_basic_cms_menu(self):
        self.assertEqual(len(menu_pool.menus), 1)
        response = self.client.get(self.get_pages_root()) # path = '/'
        self.assertEquals(response.status_code, 200)
        request = self.get_request()
        
        # test the cms menu class
        menu = CMSMenu()
        nodes = menu.get_nodes(request)
        self.assertEqual(len(nodes), len(self.get_all_pages()))
        
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
        self.assertEqual(nodes[1].get_absolute_url(), self.get_page(4).get_absolute_url())
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
        context = self.get_context(path=self.get_page(4).get_absolute_url())
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
        self.assertEqual(len(nodes), len(self.get_level(1)))
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
        context = self.get_context(path=self.get_page(3).get_absolute_url())
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
        
        page1 = Page.objects.get(pk=self.get_page(1).pk)
        page1.in_navigation = False
        page1.save()
        page2 = self.get_page(2)
        context = self.get_context(path=page2.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context) 
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(isinstance(nodes[0], NavigationNode), True)
        self.assertEqual(nodes[1].get_absolute_url(), page2.get_absolute_url())
        
    def test_11_language_chooser(self):
        # test simple language chooser with default args 
        context = self.get_context(path=self.get_page(3).get_absolute_url())
        tpl = Template("{% load menu_tags %}{% language_chooser %}")
        tpl.render(context) 
        self.assertEqual(len(context['languages']), len(settings.CMS_SITE_LANGUAGES[settings.SITE_ID]))
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
        path = self.get_page(3).get_absolute_url()
        context = self.get_context(path=path)
        tpl = Template("{%% load menu_tags %%}{%% page_language_url '%s' %%}" % settings.LANGUAGES[0][0])
        url = tpl.render(context)
        self.assertEqual(url, "/%s%s" % (settings.LANGUAGES[0][0], path))
            
    def test_13_show_menu_below_id(self):
        page2 = Page.objects.get(pk=self.get_page(2).pk)
        page2.reverse_id = "hello"
        page2.save()
        page2 = self.reload(page2)
        self.assertEqual(page2.reverse_id, "hello")
        page5 = self.get_page(5)
        context = self.get_context(path=page5.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'hello' %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        page3_url = self.get_page(3).get_absolute_url()
        self.assertEqual(nodes[0].get_absolute_url(), page3_url)
        page2.in_navigation = False
        page2.save()
        context = self.get_context(path=page5.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'hello' %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page3_url)
                    
    def test_14_unpublished(self):
        page2 = Page.objects.get(pk=self.get_page(2).pk)
        page2.published = False
        page2.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 0)
        
    def test_15_home_not_in_menu(self):
        page1 = Page.objects.get(pk=self.get_page(1).pk)
        page1.in_navigation = False
        page1.save()
        page4 = Page.objects.get(pk=self.get_page(4).pk)
        page4.in_navigation = False
        page4.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), "%s%s/" % (self.get_pages_root(), self.get_page(2).get_slug()))
        self.assertEqual(nodes[0].children[0].get_absolute_url(), "%s%s/%s/" % (self.get_pages_root(), self.get_page(2).get_slug(), self.get_page(3).get_slug()))
        page4 = Page.objects.get(pk=self.get_page(4).pk)
        page4.in_navigation = True
        page4.save()
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        
    def test_16_softroot(self):
        """
        What is a soft root?
        
            If a page is a soft root, it becomes the root page in the menu if
            we are currently on or under that page.
            
            If we are above that page, the children of this page are not shown.

        Tree from fixture:
            
            + P1
            | + P2 <- SOFTROOT
            |   + P3
            + P4
            | + P5
            + P6 (not in menu)
              + P7
              + P8
        """
        page2 = Page.objects.get(pk=self.get_page(2).pk)
        page2.soft_root = True
        page2.save()
        # current page: P2
        context = self.get_context(path=page2.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        """
        Assert that the top level contains only ONE page (P2), not 2: P1 and P4!
        """
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page2.get_absolute_url())
        # current page: P3
        page3 = Page.objects.get(pk=self.get_page(3).pk)
        context = self.get_context(path=page3.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        """
        Assert that the top level contains only ONE page (P2), not 2: P1 and P4!
        """
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), page2.get_absolute_url())
        
        # current page: P1
        page1 = Page.objects.get(pk=self.get_page(1).pk)
        context = self.get_context(path=page1.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        """
        Assert that we have two pages in root level: P1 and P4, because the
        softroot is below this level.
        """
        self.assertEqual(len(nodes), 2)
        # check that the first page is P1
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        # check that we don't show the children of P2, which is a soft root!
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
        # current page: NO PAGE
        context = self.get_context(path="/no/real/path/")
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        """
        Check behavior is the same as on P1
        """
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
        # current page: P5
        page5 = Page.objects.get(pk=self.get_page(5).pk)
        context = self.get_context(path=page5.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        """
        Again, check the behavior is the same as on P1, because we're not under
        a soft root! 
        """
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].get_absolute_url(), page1.get_absolute_url())
        self.assertEqual(len(nodes[0].children[0].children), 0)
        
    def test_17_show_submenu_from_non_menu_page(self):
        """
        Here's the structure bit we're interested in:
        
        + P6 (not in menu)
          + P7
          + P8
          
        When we render P6, there should be a menu entry for P7 and P8 if the
        tag parameters are "1 XXX XXX XXX"
        """
        page6 = Page.objects.get(pk=self.get_page(6).pk)
        context = self.get_context(page6.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 1 100 0 1 %}")
        tpl.render(context) 
        nodes = context['children']
        number_of_p6_children = len(page6.children.filter(in_navigation=True))
        self.assertEqual(len(nodes), number_of_p6_children)
        
        page7 = Page.objects.get(pk=self.get_page(7).pk)
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
        
    def test_18_show_breadcrumb_invisible(self):
        invisible_page = self.create_page(parent_page=self.get_page(3), 
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


class MenuTests(BaseMenuTest):
    def test_01_build_nodes_inner_for_worst_case_menu(self):
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
        
        final_list = _build_nodes_inner_for_one_menu(nodes, menu_class_name)
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
        
    def test_02_build_nodes_inner_for_circular_menu(self):
        '''
        TODO: 
            To properly handle this test we need to have a circular dependency 
            detection system.
            Go nuts implementing it :)
        '''
        pass
    
    def test_03_build_nodes_inner_for_broken_menu(self):
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
        
        final_list = _build_nodes_inner_for_one_menu(nodes, menu_class_name)
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

    def test_04_utils_mark_descendants(self):
        tree_nodes, flat_nodes = self._get_nodes()
        mark_descendants(tree_nodes)
        for node in flat_nodes:
            self.assertTrue(node.descendant, node)
            
    def test_05_utils_find_selected(self):
        tree_nodes, flat_nodes = self._get_nodes()
        node = flat_nodes[0]
        selected = find_selected(tree_nodes)
        self.assertEqual(selected, node)
        selected = find_selected([])
        self.assertEqual(selected, None)
        
    def test_06_utils_cut_levels(self):
        tree_nodes, flat_nodes = self._get_nodes()
        self.assertEqual(cut_levels(tree_nodes, 1), [flat_nodes[1]])
        
    def test_08_empty_menu(self):
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context) 
        nodes = context['children']
        self.assertEqual(len(nodes), 0)


class AdvancedSoftrootTests(BaseMenuTest):
    """
    Tree in fixture (as taken from issue 662):
    
        top
            root
                aaa
                    111
                        ccc
                            ddd
                    222
                bbb
                    333
                    444
    
    In the fixture, all pages are "in_navigation", "published" and
    NOT-"soft_root".
    
    What is a soft root?
    
        If a page is a soft root, it becomes the root page in the menu if
        we are currently on or under that page.
        
        If we are above that page, the children of this page are not shown.
    """
    
    def setUp(self):
        """
        For some reason turning this into a fixture just won't work (thanks to
        our dear friend, publisher).
        """
        super(AdvancedSoftrootTests, self).setUp()
        def mkpage(title, parent=None):
            page = self.create_page(parent, title=title, published=True, in_navigation=True)
            def mkchild(title):
                return mkpage(title, page)
            page.mkchild = mkchild
            return page
                
        top = mkpage('top')
        root = top.mkchild('root')
        aaa = root.mkchild('aaa')
        oneoneone = aaa.mkchild('111')
        ccc = oneoneone.mkchild('ccc')
        ccc.mkchild('ddd')
        aaa.mkchild('222')
        bbb = root.mkchild('bbb')
        bbb.mkchild('333')
        bbb.mkchild('444')
    
    def get_page(self, name):
        return Page.objects.get(title_set__slug=name)
    
    def assertTreeQuality(self, a, b, *attrs):
        """
        Checks that the node-lists a and b are the same for attrs.
        
        This is recursive over the tree
        """
        msg = '%r != %r with %r, %r' % (len(a), len(b), a, b)
        self.assertEqual(len(a), len(b), msg)
        for n1, n2 in zip(a,b):
            for attr in attrs:
                a1 = getattr(n1, attr)
                a2 = getattr(n2, attr)
                msg = '%r != %r with %r, %r (%s)' % (a1, a2, n1, n2, attr)
                self.assertEqual(a1, a2, msg)
            self.assertTreeQuality(n1.children, n2.children)
            
    def test_01_top_not_in_nav(self):
        """
        top: not in navigation
        
        tag: show_menu 0 100 0 100
        
        context shared: current page is aaa
        context 1: root is NOT a softroot
        context 2: root IS a softroot
        
        expected result: the two node-trees should be equal
        """
        top = self.get_page('top')
        top.in_navigation = False
        top.save()
        aaa = self.get_page('aaa')
        # root is NOT a soft root
        context = self.get_context(aaa.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 100 %}")
        tpl.render(context) 
        hard_root = context['children']
        # root IS a soft root
        root = self.get_page('root')
        root.soft_root = True
        root.save()
        aaa = self.get_page('aaa')
        context = self.get_context(aaa.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 100 %}")
        tpl.render(context) 
        soft_root = context['children']
        # assert the two trees are equal in terms of 'level' and 'title'
        self.assertTreeQuality(hard_root, soft_root, 'level', 'title')
            
    def test_02_top_in_nav(self):
        """
        top: in navigation
        
        tag: show_menu 0 100 0 100
        
        context shared: current page is aaa
        context 1: root is NOT a softroot
        context 2: root IS a softroot
        
        expected result 1:
            0:top
               1:root
                  2:aaa
                     3:111
                        4:ccc
                           5:ddd
                     3:222
                  2:bbb
        expected result 2:
            0:root
               1:aaa
                  2:111
                     3:ccc
                        4:ddd
                  2:222
               1:bbb
        """
        aaa = self.get_page('aaa')
        # root is NOT a soft root
        context = self.get_context(aaa.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 100 %}")
        tpl.render(context) 
        hard_root = context['children']
        mock_tree = [
            AttributeObject(title='top', level=0, children=[
                AttributeObject(title='root', level=1, children=[
                    AttributeObject(title='aaa', level=2, children=[
                        AttributeObject(title='111', level=3, children=[
                            AttributeObject(title='ccc', level=4, children=[
                                AttributeObject(title='ddd', level=5, children=[])
                            ])
                        ]),
                        AttributeObject(title='222', level=3, children=[])
                    ]),
                    AttributeObject(title='bbb', level=2, children=[])
                ])
            ])
        ]
        self.assertTreeQuality(hard_root, mock_tree)
        # root IS a soft root
        root = self.get_page('root')
        root.soft_root = True
        root.save()
        aaa = self.get_page('aaa')
        context = self.get_context(aaa.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 100 %}")
        tpl.render(context) 
        soft_root = context['children']
        mock_tree = [
            AttributeObject(title='root', level=0, children=[
                AttributeObject(title='aaa', level=1, children=[
                    AttributeObject(title='111', level=2, children=[
                        AttributeObject(title='ccc', level=3, children=[
                            AttributeObject(title='ddd', level=4, children=[])
                        ])
                    ]),
                    AttributeObject(title='222', level=2, children=[])
                ]),
                AttributeObject(title='bbb', level=1, children=[])
            ])
        ]
        self.assertTreeQuality(soft_root, mock_tree, 'title', 'level')


class ShowSubMenuCheck(BaseMenuTest):
    """
    Tree from fixture:

        + P1
        | + P2
        |   + P3
        + P4
        | + P5
        + P6
          + P7 (not in menu)
          + P8
    """
    fixtures = ['menus-sub.json']

    def test_01_show_submenu(self):
        context = self.get_context('/test-page-6/')
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_sub_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].id, 8)