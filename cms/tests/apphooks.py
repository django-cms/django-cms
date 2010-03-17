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



class ApphookTestCase(CMSTestCase):

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
        
    def test_01_basic_apphooks(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        title = page2.title_set.all()[0]
        title.application_urls = 
        
    def test_02_two_apphooks_in_different_languages(self):
        self.assertEqual(1, 2)
        