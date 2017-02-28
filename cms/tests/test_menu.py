# -*- coding: utf-8 -*-
import copy
from cms.test_utils.project.sampleapp.cms_apps import NamespacedApp, SampleApp, SampleApp2

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission, Group
from django.template import Template, TemplateSyntaxError
from django.test.utils import override_settings
from django.utils.translation import activate
from cms.apphook_pool import apphook_pool
from menus.base import NavigationNode
from menus.menu_pool import menu_pool, _build_nodes_inner_for_one_menu
from menus.models import CacheKey
from menus.utils import mark_descendants, find_selected, cut_levels

from cms.api import create_page
from cms.cms_menus import get_visible_pages
from cms.models import Page, ACCESS_PAGE_AND_DESCENDANTS
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.test_utils.project.sampleapp.cms_menus import SampleAppMenu, StaticMenu, StaticMenu2
from cms.test_utils.fixtures.menus import (MenusFixture, SubMenusFixture,
                                           SoftrootFixture, ExtendedMenusFixture)
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import apphooks, LanguageOverride
from cms.test_utils.util.mock import AttributeObject
from cms.utils import get_cms_setting
from cms.utils.i18n import force_language


class BaseMenuTest(CMSTestCase):

    def _get_nodes(self, path='/'):
        node1 = NavigationNode('1', '/1/', 1)
        node2 = NavigationNode('2', '/2/', 2, 1)
        node3 = NavigationNode('3', '/3/', 3, 2)
        node4 = NavigationNode('4', '/4/', 4, 2)
        node5 = NavigationNode('5', '/5/', 5)
        nodes = [node1, node2, node3, node4, node5]
        tree = _build_nodes_inner_for_one_menu([n for n in nodes], "test")
        request = self.get_request(path)
        renderer = menu_pool.get_renderer(request)
        renderer.apply_modifiers(tree, request)
        return tree, nodes

    def setUp(self):
        super(BaseMenuTest, self).setUp()
        if not menu_pool.discovered:
            menu_pool.discover_menus()
        self.old_menu = menu_pool.menus
        menu_pool.menus = {'CMSMenu': self.old_menu['CMSMenu']}
        menu_pool.clear(settings.SITE_ID)
        activate("en")

    def tearDown(self):
        menu_pool.menus = self.old_menu
        super(BaseMenuTest, self).tearDown()

    def get_page(self, num):
        return Page.objects.public().get(title_set__title='P%s' % num)


class MenuDiscoveryTest(ExtendedMenusFixture, CMSTestCase):

    def setUp(self):
        super(MenuDiscoveryTest, self).setUp()
        menu_pool.discovered = False
        self.old_menu = menu_pool.menus
        menu_pool.menus = {}
        menu_pool.discover_menus()
        menu_pool.register_menu(SampleAppMenu)
        menu_pool.register_menu(StaticMenu)
        menu_pool.register_menu(StaticMenu2)

    def tearDown(self):
        menu_pool.menus = self.old_menu
        super(MenuDiscoveryTest, self).tearDown()

    def test_menu_registered(self):
        menu_pool.discovered = False
        menu_pool.discover_menus()

        # The following tests that get_registered_menus()
        # returns all menus registered based on the for_rendering flag

        # A list of menu classes registered regardless of whether they
        # have instances attached or not
        registered = menu_pool.get_registered_menus(for_rendering=False)

        # A list of menu classes registered and filter out any attached menu
        # if it does not have instances.
        registered_for_rendering = menu_pool.get_registered_menus(for_rendering=True)

        # We've registered three menus
        self.assertEqual(len(registered), 3)

        # But two of those are attached menus and shouldn't be rendered.
        self.assertEqual(len(registered_for_rendering), 1)

        # Attached both menus to separate pages
        create_page("apphooked-page", "nav_playground.html", "en",
                    published=True,
                    navigation_extenders='StaticMenu')

        create_page("apphooked-page", "nav_playground.html", "en",
                    published=True,
                    navigation_extenders='StaticMenu2')

        registered = menu_pool.get_registered_menus(for_rendering=False)
        registered_for_rendering = menu_pool.get_registered_menus(for_rendering=True)

        # The count should be 3 but grows to 5 because of the two published instances.
        # Even though we've registered three menus, the total is give because two
        # are attached menus and each attached menu has two instances.
        self.assertEqual(len(registered), 5)
        self.assertEqual(len(registered_for_rendering), 5)

    def test_menu_registered_in_renderer(self):
        menu_pool.discovered = False
        menu_pool.discover_menus()

        # The following tests that a menu renderer calculates the registered
        # menus on a request basis.

        request_1 = self.get_request('/en/')
        request_1_renderer = menu_pool.get_renderer(request_1)

        registered = menu_pool.get_registered_menus(for_rendering=False)

        self.assertEqual(len(registered), 3)
        self.assertEqual(len(request_1_renderer.menus), 1)

        create_page("apphooked-page", "nav_playground.html", "en",
                    published=True,
                    navigation_extenders='StaticMenu')

        create_page("apphooked-page", "nav_playground.html", "en",
                    published=True,
                    navigation_extenders='StaticMenu2')

        request_2 = self.get_request('/en/')
        request_2_renderer = menu_pool.get_renderer(request_2)

        # The count should be 3 but grows to 5 because of the two published instances.
        self.assertEqual(len(request_2_renderer.menus), 5)

    def test_menu_expanded(self):
        menu_pool.discovered = False
        menu_pool.discover_menus()

        with self.settings(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests'):
            with apphooks(SampleApp):
                page = create_page("apphooked-page", "nav_playground.html", "en",
                                   published=True, apphook="SampleApp",
                                   navigation_extenders='StaticMenu')

                self.assertTrue(menu_pool.discovered)

                menus = menu_pool.get_registered_menus()

                self.assertTrue(menu_pool.discovered)
                # Counts the number of StaticMenu (which is expanded) and StaticMenu2
                # (which is not) and checks the key name for the StaticMenu instances
                static_menus = 2
                static_menus_2 = 1
                for key, menu in menus.items():
                    if key.startswith('StaticMenu:'):
                        static_menus -= 1
                        self.assertTrue(key.endswith(str(page.get_public_object().pk)) or key.endswith(str(page.get_draft_object().pk)))

                    if key == 'StaticMenu2':
                        static_menus_2 -= 1

                self.assertEqual(static_menus, 0)
                self.assertEqual(static_menus_2, 0)

    def test_multiple_menus(self):
        with self.settings(ROOT_URLCONF='cms.test_utils.project.urls_for_apphook_tests'):
            with apphooks(NamespacedApp, SampleApp2):
                apphook_pool.discovered = False
                apphook_pool.discover_apps()
                create_page("apphooked-page", "nav_playground.html", "en",
                            published=True, apphook="SampleApp2")
                create_page("apphooked-page", "nav_playground.html", "en",
                            published=True,
                            navigation_extenders='StaticMenu')
                create_page("apphooked-page", "nav_playground.html", "en",
                            published=True, apphook="NamespacedApp", apphook_namespace='whatever',
                            navigation_extenders='StaticMenu')
                self.assertEqual(len(menu_pool.get_menus_by_attribute("cms_enabled", True)), 2)


class ExtendedFixturesMenuTests(ExtendedMenusFixture, BaseMenuTest):
    """
    Tree from fixture:

        + P1
        | + P2
        |   + P3
        | + P9
        |   + P10
        |      + P11
        + P4
        | + P5
        + P6 (not in menu)
          + P7
          + P8
    """
    def get_page(self, num):
        return Page.objects.public().get(title_set__title='P%s' % num)

    def get_level(self, num):
        return Page.objects.public().filter(level=num)

    def get_all_pages(self):
        return Page.objects.public()

    def test_menu_failfast_on_invalid_usage(self):
        context = self.get_context()
        context['child'] = self.get_page(1)
        # test standard show_menu
        with self.settings(DEBUG=True, TEMPLATE_DEBUG=True):
            tpl = Template("{% load menu_tags %}{% show_menu 0 0 0 0 'menu/menu.html' child %}")
            self.assertRaises(TemplateSyntaxError, tpl.render, context)

    def test_show_submenu_nephews(self):
        context = self.get_context(path=self.get_page(2).get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_sub_menu 100 1 1 %}")
        tpl.render(context)
        nodes = context["children"]
        # P2 is the selected node
        self.assertTrue(nodes[0].selected)
        # Should include P10 but not P11
        self.assertEqual(len(nodes[1].children), 1)
        self.assertFalse(nodes[1].children[0].children)

        tpl = Template("{% load menu_tags %}{% show_sub_menu 100 1 %}")
        tpl.render(context)
        nodes = context["children"]
        # should now include both P10 and P11
        self.assertEqual(len(nodes[1].children), 1)
        self.assertEqual(len(nodes[1].children[0].children), 1)

    def test_show_submenu_template_root_level_none_no_nephew_limit(self):
        context = self.get_context(path=self.get_page(1).get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_sub_menu 100 None 100 %}")
        tpl.render(context)
        nodes = context["children"]
        # default nephew limit, P2 and P9 in the nodes list
        self.assertEqual(len(nodes), 2)


class FixturesMenuTests(MenusFixture, BaseMenuTest):
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
    def get_page(self, num):
        return Page.objects.public().get(title_set__title='P%s' % num)

    def get_level(self, num):
        return Page.objects.public().filter(depth=num)

    def get_all_pages(self):
        return Page.objects.public()

    def test_menu_failfast_on_invalid_usage(self):
        context = self.get_context()
        context['child'] = self.get_page(1)
        # test standard show_menu
        with self.settings(DEBUG=True, TEMPLATE_DEBUG=True):
            tpl = Template("{% load menu_tags %}{% show_menu 0 0 0 0 'menu/menu.html' child %}")
            self.assertRaises(TemplateSyntaxError, tpl.render, context)

    def test_basic_cms_menu(self):
        menus = menu_pool.get_registered_menus()
        self.assertEqual(len(menus), 1)
        with force_language("en"):
            response = self.client.get(self.get_pages_root())  # path = '/'
        self.assertEqual(response.status_code, 200)
        request = self.get_request()

        renderer = menu_pool.get_renderer(request)

        # test the cms menu class
        menu = renderer.get_menu('CMSMenu')
        nodes = menu.get_nodes(request)
        self.assertEqual(len(nodes), len(self.get_all_pages()))

    def test_show_menu(self):
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

    def test_show_menu_num_queries(self):
        context = self.get_context()
        # test standard show_menu
        with self.assertNumQueries(8):
            """
            The queries should be:
                get all public pages
                get all draft pages from public pages
                get all page permissions
                get all titles
                get the menu cache key
                create a savepoint
                set the menu cache key
                release the savepoint
            """
            tpl = Template("{% load menu_tags %}{% show_menu %}")
            tpl.render(context)

    def test_show_menu_cache_key_leak(self):
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        self.assertEqual(CacheKey.objects.count(), 0)
        tpl.render(context)
        self.assertEqual(CacheKey.objects.count(), 1)
        tpl.render(context)
        self.assertEqual(CacheKey.objects.count(), 1)

    def test_menu_keys_duplicate_truncates(self):
        """
        When two objects with the same characteristics are present in the
        database, get_or_create truncates the database table to "invalidate"
        the cache, before retrying. This can happen after migrations, and since
        it's only cache, we don't want any propagation of errors.
        """
        CacheKey.objects.create(language="fr", site=1, key="a")
        CacheKey.objects.create(language="fr", site=1, key="a")
        CacheKey.objects.get_or_create(language="fr", site=1, key="a")

        self.assertEqual(CacheKey.objects.count(), 1)

    def test_only_active_tree(self):
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

    def test_only_one_active_level(self):
        context = self.get_context()
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 0 1 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes[1].children), 0)
        self.assertEqual(len(nodes[0].children), 1)
        self.assertEqual(len(nodes[0].children[0].children), 0)

    def test_only_level_zero(self):
        context = self.get_context()
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_menu 0 0 0 0 %}")
        tpl.render(context)
        nodes = context['children']
        for node in nodes:
            self.assertEqual(len(node.children), 0)

    def test_only_level_one(self):
        context = self.get_context()
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_menu 1 1 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), len(self.get_level(2)))
        for node in nodes:
            self.assertEqual(len(node.children), 0)

    def test_only_level_one_active(self):
        context = self.get_context()
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_menu 1 1 0 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].descendant, True)
        self.assertEqual(len(nodes[0].children), 0)

    def test_level_zero_and_one(self):
        context = self.get_context()
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_menu 0 1 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            self.assertEqual(len(node.children), 1)

    def test_show_submenu(self):
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

        context = self.get_context(path=self.get_page(3).get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_sub_menu 100 1 %}")
        tpl.render(context)
        nodes = context["children"]
        # P3 is the selected node
        self.assertFalse(nodes[0].selected)
        self.assertTrue(nodes[0].children[0].selected)
        # top level node should be P2
        self.assertEqual(nodes[0].get_absolute_url(), self.get_page(2).get_absolute_url())
        # should include P3 as well
        self.assertEqual(len(nodes[0].children), 1)

        context = self.get_context(path=self.get_page(2).get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_sub_menu 100 0 %}")
        tpl.render(context)
        nodes = context["children"]
        # P1 should be in the nav
        self.assertEqual(nodes[0].get_absolute_url(), self.get_page(1).get_absolute_url())
        # P2 is selected
        self.assertTrue(nodes[0].children[0].selected)

    def test_show_submenu_template_root_level_none(self):
        context = self.get_context(path=self.get_page(1).get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_sub_menu 100 None 1 %}")
        tpl.render(context)
        nodes = context["children"]
        # First node is P2 (P1 children) thus not selected
        self.assertFalse(nodes[0].selected)
        # nephew limit of 1, so only P2 is the nodes list
        self.assertEqual(len(nodes), 1)
        # P3 is a child of P2, but not in nodes list
        self.assertTrue(nodes[0].children)

    def test_show_breadcrumb(self):
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

        page1 = self.get_page(1)
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

    def test_language_chooser(self):
        # test simple language chooser with default args
        lang_settings = copy.deepcopy(get_cms_setting('LANGUAGES'))
        lang_settings[1][0]['public'] = False
        with self.settings(CMS_LANGUAGES=lang_settings):
            context = self.get_context(path=self.get_page(3).get_absolute_url())
            tpl = Template("{% load menu_tags %}{% language_chooser %}")
            tpl.render(context)
            self.assertEqual(len(context['languages']), 3)
            # try a different template and some different args
            tpl = Template("{% load menu_tags %}{% language_chooser 'menu/test_language_chooser.html' %}")
            tpl.render(context)
            self.assertEqual(context['template'], 'menu/test_language_chooser.html')
            tpl = Template("{% load menu_tags %}{% language_chooser 'short' 'menu/test_language_chooser.html' %}")
            tpl.render(context)
            self.assertEqual(context['template'], 'menu/test_language_chooser.html')
            for lang in context['languages']:
                self.assertEqual(*lang)

    def test_page_language_url(self):
        path = self.get_page(3).get_absolute_url()
        context = self.get_context(path=path)
        tpl = Template("{%% load menu_tags %%}{%% page_language_url '%s' %%}" % 'en')
        url = tpl.render(context)
        self.assertEqual(url, "%s" % path)

    def test_show_menu_below_id(self):
        page2 = self.get_page(2)
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

    def test_unpublished(self):
        page2 = self.get_page(2)
        page2.title_set.update(published=False)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 0)

    def test_home_not_in_menu(self):
        page1 = self.get_page(1)
        page1.in_navigation = False
        page1.save()
        page4 = self.get_page(4)
        page4.in_navigation = False
        page4.save()
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get_absolute_url(), self.get_page(2).get_absolute_url())
        self.assertEqual(nodes[0].children[0].get_absolute_url(), self.get_page(3).get_absolute_url())
        page4 = self.get_page(4)
        page4.in_navigation = True
        page4.save()
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)

    def test_show_submenu_from_non_menu_page(self):
        """
        Here's the structure bit we're interested in:

        + P6 (not in menu)
          + P7
          + P8

        When we render P6, there should be a menu entry for P7 and P8 if the
        tag parameters are "1 XXX XXX XXX"
        """
        page6 = self.get_page(6)
        context = self.get_context(page6.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 1 100 0 1 %}")
        tpl.render(context)
        nodes = context['children']
        number_of_p6_children = len(page6.children.filter(in_navigation=True))
        self.assertEqual(len(nodes), number_of_p6_children)

        page7 = self.get_page(7)
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

    def test_show_breadcrumb_invisible(self):
        # Must use the drafts to find the parent when calling create_page
        parent = Page.objects.drafts().get(title_set__title='P3')
        invisible_page = create_page("invisible", "nav_playground.html", "en",
            parent=parent, published=True, in_navigation=False)
        context = self.get_context(path=invisible_page.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context)
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 3)
        tpl = Template("{% load menu_tags %}{% show_breadcrumb 0 'menu/breadcrumb.html' 1 %}")
        tpl.render(context)
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 3)
        tpl = Template("{% load menu_tags %}{% show_breadcrumb 0 'menu/breadcrumb.html' 0 %}")
        tpl.render(context)
        nodes = context['ancestors']
        self.assertEqual(len(nodes), 4)


class MenuTests(BaseMenuTest):

    def test_build_nodes_inner_for_worst_case_menu(self):
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
        nodes = [node1, node2, node3, node4, node5, ]
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

    def test_build_nodes_inner_for_circular_menu(self):
        '''
        TODO:
            To properly handle this test we need to have a circular dependency
            detection system.
            Go nuts implementing it :)
        '''
        pass

    def test_build_nodes_inner_for_broken_menu(self):
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
        nodes = [node1, node2, node3, node4, node5, ]

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

    def test_utils_mark_descendants(self):
        tree_nodes, flat_nodes = self._get_nodes()
        mark_descendants(tree_nodes)
        for node in flat_nodes:
            self.assertTrue(node.descendant, node)

    def test_utils_find_selected(self):
        tree_nodes, flat_nodes = self._get_nodes()
        node = flat_nodes[0]
        selected = find_selected(tree_nodes)
        self.assertEqual(selected, node)
        selected = find_selected([])
        self.assertEqual(selected, None)

    def test_utils_cut_levels(self):
        tree_nodes, flat_nodes = self._get_nodes()
        self.assertEqual(cut_levels(tree_nodes, 1), [flat_nodes[1]])

    def test_empty_menu(self):
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 0)


@override_settings(CMS_PERMISSION=False)
class AdvancedSoftrootTests(SoftrootFixture, CMSTestCase):
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

    def tearDown(self):
        Page.objects.all().delete()

    def get_page(self, name):
        return Page.objects.public().get(title_set__slug=name)

    def assertTreeQuality(self, a, b, *attrs):
        """
        Checks that the node-lists a and b are the same for attrs.

        This is recursive over the tree
        """
        msg = '%r != %r with %r, %r' % (len(a), len(b), a, b)
        self.assertEqual(len(a), len(b), msg)
        for n1, n2 in zip(a, b):
            for attr in attrs:
                a1 = getattr(n1, attr)
                a2 = getattr(n2, attr)
                msg = '%r != %r with %r, %r (%s)' % (a1, a2, n1, n2, attr)
                self.assertEqual(a1, a2, msg)
            self.assertTreeQuality(n1.children, n2.children)

    def test_top_not_in_nav(self):
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

    def test_top_in_nav(self):
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


class ShowSubMenuCheck(SubMenusFixture, BaseMenuTest):
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
    def test_show_submenu(self):
        page = self.get_page(6)
        subpage = self.get_page(8)
        context = self.get_context(page.get_absolute_url())
        # test standard show_menu
        tpl = Template("{% load menu_tags %}{% show_sub_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].id, subpage.pk)

    def test_show_submenu_num_queries(self):
        page = self.get_page(6)
        subpage = self.get_page(8)
        context = self.get_context(page.get_absolute_url())

        # test standard show_menu
        with self.assertNumQueries(8):
            """
            The queries should be:
                get all public pages
                get all draft pages for public pages
                get all page permissions
                get all titles
                get the menu cache key
                create a savepoint
                set the menu cache key
                release the savepoint
            """
            tpl = Template("{% load menu_tags %}{% show_sub_menu %}")
            tpl.render(context)
            nodes = context['children']
            self.assertEqual(len(nodes), 1)
            self.assertEqual(nodes[0].id, subpage.pk)


class ShowMenuBelowIdTests(BaseMenuTest):
    """
    Test for issue 521

    Build the following tree:

        A
        |-B
          |-C
          \-D (not in nav)
    """
    def test_not_in_navigation(self):
        a = create_page('A', 'nav_playground.html', 'en', published=True,
                        in_navigation=True, reverse_id='a')
        b = create_page('B', 'nav_playground.html', 'en', parent=a,
                       published=True, in_navigation=True)
        c = create_page('C', 'nav_playground.html', 'en', parent=b,
                        published=True, in_navigation=True)
        create_page('D', 'nav_playground.html', 'en', parent=self.reload(b),
                    published=True, in_navigation=False)
        context = self.get_context(a.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1, nodes)
        node = nodes[0]
        self.assertEqual(node.id, b.publisher_public.id)
        children = node.children
        self.assertEqual(len(children), 1, repr(children))
        child = children[0]
        self.assertEqual(child.id, c.publisher_public.id)

    def test_menu_beyond_soft_root(self):
        """
        Test for issue 4107

        Build the following tree:

            A
            |-B (soft_root)
              |-C
        """
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        a = create_page('A', reverse_id='a', **stdkwargs)
        b = create_page('B', parent=a, soft_root=True, **stdkwargs)
        c = create_page('C', parent=b, **stdkwargs)

        context = self.get_context(a.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check whole menu
        self.assertEqual(len(nodes), 1)
        a_node = nodes[0]
        self.assertEqual(a_node.id, a.publisher_public.pk)  # On A, show from A
        self.assertEqual(len(a_node.children), 1)
        b_node = a_node.children[0]
        self.assertEqual(b_node.id, b.publisher_public.pk)
        self.assertEqual(len(b_node.children), 1)
        c_node = b_node.children[0]
        self.assertEqual(c_node.id, c.publisher_public.pk)
        self.assertEqual(len(c_node.children), 0)

        context = self.get_context(b.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check whole menu
        self.assertEqual(len(nodes), 1)
        b_node = nodes[0]
        self.assertEqual(b_node.id, b.publisher_public.pk)  # On B, show from B
        self.assertEqual(len(b_node.children), 1)
        c_node = b_node.children[0]
        self.assertEqual(c_node.id, c.publisher_public.pk)
        self.assertEqual(len(c_node.children), 0)

        context = self.get_context(c.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check whole menu
        self.assertEqual(len(nodes), 1)
        b_node = nodes[0]
        self.assertEqual(b_node.id, b.publisher_public.pk)  # On C, show from B
        self.assertEqual(len(b_node.children), 1)
        c_node = b_node.children[0]
        self.assertEqual(c_node.id, c.publisher_public.pk)
        self.assertEqual(len(c_node.children), 0)

        context = self.get_context(a.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check whole menu
        self.assertEqual(len(nodes), 1)
        b_node = nodes[0]
        self.assertEqual(b_node.id, b.publisher_public.pk)  # On A, show from B (since below A)
        self.assertEqual(len(b_node.children), 1)
        c_node = b_node.children[0]
        self.assertEqual(c_node.id, c.publisher_public.pk)
        self.assertEqual(len(c_node.children), 0)

        context = self.get_context(b.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check whole menu
        self.assertEqual(len(nodes), 1)
        b_node = nodes[0]
        self.assertEqual(b_node.id, b.publisher_public.pk)  # On B, show from B (since below A)
        self.assertEqual(len(b_node.children), 1)
        c_node = b_node.children[0]
        self.assertEqual(c_node.id, c.publisher_public.pk)
        self.assertEqual(len(c_node.children), 0)

        context = self.get_context(c.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check whole menu
        self.assertEqual(len(nodes), 1)
        b_node = nodes[0]
        self.assertEqual(b_node.id, b.publisher_public.pk)  # On C, show from B (since below A)
        self.assertEqual(len(b_node.children), 1)
        c_node = b_node.children[0]
        self.assertEqual(c_node.id, c.publisher_public.pk)
        self.assertEqual(len(c_node.children), 0)

    def test_not_in_navigation_num_queries(self):
        """
        Test for issue 521

        Build the following tree:

            A
            |-B
              |-C
              \-D (not in nav)
        """
        a = create_page('A', 'nav_playground.html', 'en', published=True,
                        in_navigation=True, reverse_id='a')
        b = create_page('B', 'nav_playground.html', 'en', parent=a,
                        published=True, in_navigation=True)
        c = create_page('C', 'nav_playground.html', 'en', parent=b,
                        published=True, in_navigation=True)
        create_page('D', 'nav_playground.html', 'en', parent=self.reload(b),
                    published=True, in_navigation=False)

        with LanguageOverride('en'):
            context = self.get_context(a.get_absolute_url())
            with self.assertNumQueries(8):
                """
                The queries should be:
                    get all public pages
                    get all draft pages for public pages
                    get all page permissions
                    get all titles
                    get the menu cache key
                    create a savepoint
                    set the menu cache key
                    release the savepoint
                """
                # Actually seems to run:
                tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' 0 100 100 100 %}")
                tpl.render(context)
            nodes = context['children']
            self.assertEqual(len(nodes), 1, nodes)
            node = nodes[0]
            self.assertEqual(node.id, b.publisher_public.id)
            children = node.children
            self.assertEqual(len(children), 1, repr(children))
            child = children[0]
            self.assertEqual(child.id, c.publisher_public.id)

    def test_menu_in_soft_root(self):
        """
        Test for issue 3504

        Build the following tree:

            A
            |-B
            C (soft_root)
        """
        a = create_page('A', 'nav_playground.html', 'en', published=True,
                        in_navigation=True, reverse_id='a')
        b = create_page('B', 'nav_playground.html', 'en', parent=a,
                       published=True, in_navigation=True)
        c = create_page('C', 'nav_playground.html', 'en', published=True,
                        in_navigation=True, soft_root=True)
        context = self.get_context(a.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(node.id, b.publisher_public.id)
        context = self.get_context(c.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu_below_id 'a' %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(node.id, b.publisher_public.id)


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='staff',
)
class ViewPermissionMenuTests(CMSTestCase):

    def setUp(self):
        self.page = create_page('page', 'nav_playground.html', 'en')
        self.pages = [self.page]
        self.user = self.get_standard_user()

    def get_request(self, user=None):
        attrs = {
            'user': user or AnonymousUser(),
            'REQUEST': {},
            'POST': {},
            'GET': {},
            'session': {},
        }
        return type('Request', (object,), attrs)

    def test_public_for_all_staff(self):
        request = self.get_request(self.user)
        request.user.is_staff = True
        with self.assertNumQueries(4):
            """
            The queries are:
            User permissions
            Content type
            GlobalPagePermission query
            PagePermission count query
            """
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [self.page.pk])

    @override_settings(CMS_PUBLIC_FOR='all')
    def test_public_for_all(self):
        request = self.get_request(self.user)

        with self.assertNumQueries(4):
            """
            The queries are:
            User permissions
            Content type
            GlobalPagePermission query
            PagePermission query for affected pages
            """
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [self.page.pk])

    @override_settings(CMS_PUBLIC_FOR='all')
    def test_unauthed(self):
        request = self.get_request()
        with self.assertNumQueries(1):
            """
            The query is:
            PagePermission query for affected pages
            """
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [self.page.pk])

    def test_authed_basic_perm(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_page'))
        request = self.get_request(self.user)

        with self.assertNumQueries(2):
            """
            The queries are:
            User permissions
            Content type
            """
            result = get_visible_pages(request, self.pages, self.page.site)
            self.assertEqual(result, [self.page.pk])

    def test_authed_no_access(self):
        request = self.get_request(self.user)

        with self.assertNumQueries(4):
            """
            The queries are:
            View Permission Calculation Query
            GlobalpagePermission query for user
            User permissions
            Content type
            """
            result = get_visible_pages(request, self.pages, self.page.site)
            self.assertEqual(result, [])

    def test_unauthed_no_access(self):
        request = self.get_request()

        with self.assertNumQueries(0):
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [])

    def test_page_permissions(self):
        request = self.get_request(self.user)
        PagePermission.objects.create(can_view=True, user=self.user, page=self.page)

        with self.assertNumQueries(4):
            """
            The queries are:
            PagePermission query for affected pages
            User permissions
            Content type
            GlobalpagePermission query for user
            """
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [self.page.pk])

    def test_page_permissions_view_groups(self):
        group = Group.objects.create(name='testgroup')
        self.user.groups.add(group)
        request = self.get_request(self.user)
        PagePermission.objects.create(can_view=True, group=group, page=self.page)

        with self.assertNumQueries(5):
            """
            The queries are:
            PagePermission query for affected pages
            User permissions
            Content type
            GlobalpagePermission query for user
            Group query via PagePermission
            """
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [self.page.pk])

    def test_global_permission(self):
        GlobalPagePermission.objects.create(can_view=True, user=self.user)
        request = self.get_request(self.user)
        group = Group.objects.create(name='testgroup')
        PagePermission.objects.create(can_view=True, group=group, page=self.page)

        with self.assertNumQueries(3):
            """
            The queries are:
            User permissions
            Content type
            GlobalpagePermission query for user
            """
            result = get_visible_pages(request, self.pages)
            self.assertEqual(result, [self.page.pk])


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='all',
)
class PublicViewPermissionMenuTests(CMSTestCase):

    def setUp(self):
        """
        Create this published hierarchy:
        A
        B1     B2
        C1 C2  C3 C4
        """
        l = 'nav_playground.html'
        kw = dict(published=True, in_navigation=True)
        a = create_page('a', l, 'en', **kw)
        b1 = create_page('b1', l, 'en', parent=a, **kw)
        b2 = create_page('b2', l, 'en', parent=a, **kw)
        c1 = create_page('c1', l, 'en', parent=b1, **kw)
        c2 = create_page('c2', l, 'en', parent=b1, **kw)
        c3 = create_page('c3', l, 'en', parent=b2, **kw)
        c4 = create_page('c4', l, 'en', parent=b2, **kw)
        self.pages = [a, b1, c1, c2, b2, c3, c4] # tree order
        self.site = a.site

        self.user = self._create_user("standard", is_staff=False, is_superuser=False)
        self.other = self._create_user("other", is_staff=False, is_superuser=False)
        PagePermission.objects.create(page=b1, user=self.user, can_view=True,
                                      grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        PagePermission.objects.create(page=b2, user=self.other, can_view=True,
                                      grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        attrs = {
            'user': self.user,
            'REQUEST': {},
            'POST': {},
            'GET': {},
            'session': {},
        }
        self.request = type('Request', (object,), attrs)

    def test_draft_list_access(self):
        result = get_visible_pages(self.request, self.pages, self.site)
        pages = Page.objects.filter(id__in=result).values_list('title_set__title', flat=True)
        pages = list(pages)
        self.assertEqual(pages, ['a', 'b1', 'c1', 'c2'])

    def test_draft_qs_access(self):
        result = get_visible_pages(self.request, Page.objects.drafts(), self.site)
        pages = Page.objects.filter(id__in=result).values_list('title_set__title', flat=True)
        pages = list(pages)
        self.assertEqual(pages, ['a', 'b1', 'c1', 'c2'])

    def test_public_qs_access(self):
        result = get_visible_pages(self.request, Page.objects.public(), self.site)
        pages = Page.objects.filter(id__in=result).values_list('title_set__title', flat=True)
        pages = list(pages)
        self.assertEqual(pages, ['a', 'b1', 'c1', 'c2'])


@override_settings(CMS_PERMISSION=False)
class SoftrootTests(CMSTestCase):
    """
    Ask evildmp/superdmp if you don't understand softroots!

    Softroot description from the docs:

        A soft root is a page that acts as the root for a menu navigation tree.

        Typically, this will be a page that is the root of a significant new
        section on your site.

        When the soft root feature is enabled, the navigation menu for any page
        will start at the nearest soft root, rather than at the real root of
        the site’s page hierarchy.

        This feature is useful when your site has deep page hierarchies (and
        therefore multiple levels in its navigation trees). In such a case, you
        usually don’t want to present site visitors with deep menus of nested
        items.

        For example, you’re on the page “Introduction to Bleeding”, so the menu
        might look like this:

            School of Medicine
                Medical Education
                Departments
                    Department of Lorem Ipsum
                    Department of Donec Imperdiet
                    Department of Cras Eros
                    Department of Mediaeval Surgery
                        Theory
                        Cures
                        Bleeding
                            Introduction to Bleeding <this is the current page>
                            Bleeding - the scientific evidence
                            Cleaning up the mess
                            Cupping
                            Leaches
                            Maggots
                        Techniques
                        Instruments
                    Department of Curabitur a Purus
                    Department of Sed Accumsan
                    Department of Etiam
                Research
                Administration
                Contact us
                Impressum

        which is frankly overwhelming.

        By making “Department of Mediaeval Surgery” a soft root, the menu
        becomes much more manageable:

            Department of Mediaeval Surgery
                Theory
                Cures
                    Bleeding
                        Introduction to Bleeding <current page>
                        Bleeding - the scientific evidence
                        Cleaning up the mess
                    Cupping
                    Leaches
                    Maggots
                Techniques
                Instruments
    """

    def test_basic_home(self):
        """
        Given the tree:

        |- Home
        | |- Projects (SOFTROOT)
        | | |- django CMS
        | | |- django Shop
        | |- People

        Expected menu when on "Home" (0 100 100 100):

        |- Home
        | |- Projects (SOFTROOT)
        | | |- django CMS
        | | |- django Shop
        | |- People
        """
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        home = create_page("Home", **stdkwargs)
        projects = create_page("Projects", parent=home, soft_root=True, **stdkwargs)
        djangocms = create_page("django CMS", parent=projects, **stdkwargs)
        djangoshop = create_page("django Shop", parent=projects, **stdkwargs)
        people = create_page("People", parent=home, **stdkwargs)
        # On Home
        context = self.get_context(home.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check everything
        self.assertEqual(len(nodes), 1)
        homenode = nodes[0]
        self.assertEqual(homenode.id, home.publisher_public.pk)
        self.assertEqual(len(homenode.children), 2)
        projectsnode, peoplenode = homenode.children
        self.assertEqual(projectsnode.id, projects.publisher_public.pk)
        self.assertEqual(peoplenode.id, people.publisher_public.pk)
        self.assertEqual(len(projectsnode.children), 2)
        cmsnode, shopnode = projectsnode.children
        self.assertEqual(cmsnode.id, djangocms.publisher_public.pk)
        self.assertEqual(shopnode.id, djangoshop.publisher_public.pk)
        self.assertEqual(len(cmsnode.children), 0)
        self.assertEqual(len(shopnode.children), 0)
        self.assertEqual(len(peoplenode.children), 0)

    def test_basic_projects(self):
        """
        Given the tree:

        |- Home
        | |- Projects (SOFTROOT)
        | | |- django CMS
        | | |- django Shop
        | |- People

        Expected menu when on "Projects" (0 100 100 100):

        |- Projects (SOFTROOT)
        | |- django CMS
        | |- django Shop
        """
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        home = create_page("Home", **stdkwargs)
        projects = create_page("Projects", parent=home, soft_root=True, **stdkwargs)
        djangocms = create_page("django CMS", parent=projects, **stdkwargs)
        djangoshop = create_page("django Shop", parent=projects, **stdkwargs)
        create_page("People", parent=home, **stdkwargs)
        # On Projects
        context = self.get_context(projects.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check everything
        self.assertEqual(len(nodes), 1)
        projectsnode = nodes[0]
        self.assertEqual(projectsnode.id, projects.publisher_public.pk)
        self.assertEqual(len(projectsnode.children), 2)
        cmsnode, shopnode = projectsnode.children
        self.assertEqual(cmsnode.id, djangocms.publisher_public.pk)
        self.assertEqual(shopnode.id, djangoshop.publisher_public.pk)
        self.assertEqual(len(cmsnode.children), 0)
        self.assertEqual(len(shopnode.children), 0)

    def test_basic_djangocms(self):
        """
        Given the tree:

        |- Home
        | |- Projects (SOFTROOT)
        | | |- django CMS
        | | |- django Shop
        | |- People

        Expected menu when on "django CMS" (0 100 100 100):

        |- Projects (SOFTROOT)
        | |- django CMS
        | |- django Shop
        """
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        home = create_page("Home", **stdkwargs)
        projects = create_page("Projects", parent=home, soft_root=True, **stdkwargs)
        djangocms = create_page("django CMS", parent=projects, **stdkwargs)
        djangoshop = create_page("django Shop", parent=projects, **stdkwargs)
        create_page("People", parent=home, **stdkwargs)
        # On django CMS
        context = self.get_context(djangocms.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check everything
        self.assertEqual(len(nodes), 1)
        projectsnode = nodes[0]
        self.assertEqual(projectsnode.id, projects.publisher_public.pk)
        self.assertEqual(len(projectsnode.children), 2)
        cmsnode, shopnode = projectsnode.children
        self.assertEqual(cmsnode.id, djangocms.publisher_public.pk)
        self.assertEqual(shopnode.id, djangoshop.publisher_public.pk)
        self.assertEqual(len(cmsnode.children), 0)
        self.assertEqual(len(shopnode.children), 0)

    def test_basic_people(self):
        """
        Given the tree:

        |- Home
        | |- Projects (SOFTROOT)
        | | |- django CMS
        | | |- django Shop
        | |- People

        Expected menu when on "People" (0 100 100 100):

        |- Home
        | |- Projects (SOFTROOT)
        | | |- django CMS
        | | |- django Shop
        | |- People
        """
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        home = create_page("Home", **stdkwargs)
        projects = create_page("Projects", parent=home, soft_root=True, **stdkwargs)
        djangocms = create_page("django CMS", parent=projects, **stdkwargs)
        djangoshop = create_page("django Shop", parent=projects, **stdkwargs)
        people = create_page("People", parent=home, **stdkwargs)
        # On People
        context = self.get_context(home.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        # check everything
        self.assertEqual(len(nodes), 1)
        homenode = nodes[0]
        self.assertEqual(homenode.id, home.publisher_public.pk)
        self.assertEqual(len(homenode.children), 2)
        projectsnode, peoplenode = homenode.children
        self.assertEqual(projectsnode.id, projects.publisher_public.pk)
        self.assertEqual(peoplenode.id, people.publisher_public.pk)
        self.assertEqual(len(projectsnode.children), 2)
        cmsnode, shopnode = projectsnode.children
        self.assertEqual(cmsnode.id, djangocms.publisher_public.pk)
        self.assertEqual(shopnode.id, djangoshop.publisher_public.pk)
        self.assertEqual(len(cmsnode.children), 0)
        self.assertEqual(len(shopnode.children), 0)
        self.assertEqual(len(peoplenode.children), 0)
