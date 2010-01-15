# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from cms.models import Page
from menus.templatetags.menu_tags import show_menu
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from django.test import TestCase
from cms.tests.base import CMSTestCase

class NavExtenderTestCase(CMSTestCase):

    fixtures = ['test_navextender', ]
    #urls = 'example.sampleapp.urlstwo'
    
    PK_ROOT = 8
    PK_NORMAL = 15
    PK_EXTENDED = 10
    
    def setUp(self):
        self.context = self.get_context()
    
    def _prepage_page_pk(self, page_pk):
        self.context['request'].current_page = Page.objects.get(pk = page_pk)
        
    def test_submenu_root(self):
        """
        Checks if the submenu works correctly with root_page
        """

        self._prepage_page_pk(self.PK_ROOT)
        result = show_menu(self.context, 0, 100, 0, 1)

        # we expect page "Home" with attribute "childrens" containing two pages
        children = result['children']
        self.assertEqual(len(children), 1, 'Expecting only the root-page to be in children')
        p = children[0]
        self.assertEqual(p.pk, self.PK_ROOT, 'Expecting pk to be %s' % self.PK_ROOT)
        
        # checking childrens
        self.assertEqual(len(p.childrens), 2, 'Expecting two menu entries')
        self.assertEqual(p.childrens[0].pk, self.PK_EXTENDED)
        self.assertEqual(p.childrens[1].pk, self.PK_NORMAL)
        
        # with no submenu entrie
        for child in p.childrens:
            self.assertEqual(len(child.childrens), 0, 'Expecting no submenu entries')
        

    def test_submenu_normal(self):
        """
        Checks the submenu for normal pages (without nav extenders)
        """
        
        self._prepage_page_pk(self.PK_NORMAL)
        result = show_menu(self.context, 0, 100, 0, 1)

        children = result['children']
        self.assertEqual(len(children), 1, 'Expecting only the root-page to be in children')
        p = children[0]
        self.assertEqual(p.pk, self.PK_ROOT, 'Expecting pk to be %s' % self.PK_ROOT)
        
        # checking childrens of root page
        self.assertEqual(len(p.childrens), 2, 'Expecting two menu entries')
        self.assertEqual(p.childrens[0].pk, self.PK_EXTENDED)
        self.assertEqual(p.childrens[1].pk, self.PK_NORMAL)

        # extended should have no children
        self.assertEqual(len(p.childrens[0].childrens), 0, 
                         'Extended page\'s children should not be visible. %s' % self._string_result(result))
        self.assertEqual(len(p.childrens[1].childrens), 2, 'Children of normal page should be visible')
        


    def test_submenu_extended(self):
        """
        Checks the submenu of the extended page
        """
        self._prepage_page_pk(self.PK_EXTENDED)
        result = show_menu(self.context, 0, 100, 0, 1)
        
        children = result['children']
        self.assertEqual(len(children), 1, 'Expecting only the root-page to be in children')
        p = children[0]
        self.assertEqual(p.pk, self.PK_ROOT, 'Expecting pk to be %s' % self.PK_ROOT)
        
        # checking childrens of root page
        self.assertEqual(len(p.childrens), 2, 'Expecting two menu entries')
        self.assertEqual(p.childrens[0].pk, self.PK_EXTENDED)
        self.assertEqual(p.childrens[1].pk, self.PK_NORMAL)

        # extended should have no children
        self.assertEqual(len(p.childrens[0].childrens), 2, 
                         'Extended page\'s children should be visible. %s' % self._string_result(result))
        self.assertEqual(len(p.childrens[1].childrens), 0, 'Children of normal page should not be visible')
        
    def _string_result(self, result):
        # check result
        retval = []
        retval.append("Got Result:")
        for c in result['children']:
            retval.append(self._string_page(c))
        return ' '.join(retval)
            
    def _string_page(self, page):
            retval = []
            # add pk to display
            #retval.append("%s, %s" % (repr(page), getattr(page, 'pk', 'NAVNODE')))
            retval.append("%s" % (repr(page),))
            for c in page.childrens:
                retval.append(self._string_page(c))
            return ' '.join(retval)
        