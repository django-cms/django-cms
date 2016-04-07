# -*- coding: utf-8 -*-
from __future__ import with_statement

from django.template import Template

from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase, ClearURLs
from cms.templatetags.cms_admin import preview_link
from cms.utils.i18n import force_language
from django.test.utils import override_settings
from menus.base import NavigationNode


@override_settings(ROOT_URLCONF='cms.test_utils.project.nonroot_urls')
class NonRootCase(ClearURLs, CMSTestCase):
    def setUp(self):
        u = self._create_user("test", True, True)

        with self.login_user_context(u):
            self.create_some_pages()

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

    def test_get_page_root(self):
        self.assertEqual(self.get_pages_root(), '/en/content/')

    def test_basic_cms_menu(self):
        response = self.client.get(self.get_pages_root())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_pages_root(), "/en/content/")

    def test_show_menu(self):
        context = self.get_context()
        tpl = Template("{% load menu_tags %}{% show_menu %}")
        tpl.render(context)
        nodes = context['children']
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(nodes[0].get_absolute_url(), "/en/content/")

    def test_show_breadcrumb(self):
        page2 = Page.objects.get(pk=self.page2.pk)
        context = self.get_context(path=self.page2.get_absolute_url())
        tpl = Template("{% load menu_tags %}{% show_breadcrumb %}")
        tpl.render(context)
        nodes = context['ancestors']
        self.assertEqual(nodes[0].get_absolute_url(), self.get_pages_root())
        self.assertEqual(nodes[0].get_absolute_url(), "/en/content/")
        self.assertEqual(isinstance(nodes[0], NavigationNode), True)
        self.assertEqual(nodes[1].get_absolute_url(), page2.get_absolute_url())

    def test_form_multilingual_admin(self):
        """
        Tests for correct form URL mangling in preview_link templatetag
        """
        language = 'en'
        with force_language("en"):
            pages_root = self.get_pages_root()
            link = preview_link(self.page2,language=language)
        self.assertEqual(link,'%s%s/' % (pages_root,self.page2.get_slug()))
        self.assertEqual(link,'/en/content/page2/')
