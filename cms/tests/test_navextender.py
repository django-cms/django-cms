from django.conf import settings
from django.template import Template

from cms.models import Page
from cms.test_utils.fixtures.navextenders import NavextendersFixture
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.menu_extender import TestMenu
from menus.menu_pool import menu_pool


class NavExtenderTestCase(NavextendersFixture, CMSTestCase):

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
        menu_pool.menus = {
            'CMSMenu': self.old_menu['CMSMenu'],
            'TestMenu': TestMenu
        }

    def tearDown(self):
        menu_pool.menus = self.old_menu

    def _get_page(self, num):
        return Page.objects.get(title_set__title='page%s' % num)

    def _update_page(self, num, **stuff):
        Page.objects.filter(title_set__title='page%s' % num).update(**stuff)

    def test_menu_registration(self):
        self.assertEqual(len(menu_pool.menus), 2)
        self.assertEqual(len(menu_pool.modifiers) >= 4, True)

    def test_extenders_on_root(self):
        self._update_page(1, navigation_extenders="TestMenu")
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()

        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(len(nodes[0].children[3].children), 1)
        self._update_page(1, in_navigation=False)
        menu_pool.clear(settings.SITE_ID)
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 5)

    def test_extenders_on_root_child(self):
        self._update_page(4, navigation_extenders="TestMenu")
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
        self._update_page(1, in_navigation=False)
        self._update_page(2, navigation_extenders="TestMenu")
        menu_pool.clear(settings.SITE_ID)
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].children), 4)
        self.assertEqual(nodes[0].children[1].get_absolute_url(), "/")

    def test_incorrect_nav_extender_in_db(self):
        self._update_page(2, navigation_extenders="SomethingWrong")
        menu_pool.clear(settings.SITE_ID)
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(len(nodes), 2)
