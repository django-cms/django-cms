# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.models.pagemodel import Page
from cms.test_utils.util.context_managers import SettingsOverride


class MenusFixture(object):
    def create_fixtures(self):
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
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',            
        }
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            p1 = create_page('P1', published=True, in_navigation=True, **defaults)
            p4 = create_page('P4', published=True, in_navigation=True, **defaults)
            p6 = create_page('P6', published=True, in_navigation=False, **defaults)
            p1 = Page.objects.get(pk=p1.pk)
            p2 = create_page('P2', published=True, in_navigation=True, parent=p1, **defaults)
            create_page('P3', published=True, in_navigation=True, parent=p2, **defaults)
            p4 = Page.objects.get(pk=p4.pk)
            create_page('P5', published=True, in_navigation=True, parent=p4, **defaults)
            p6 = Page.objects.get(pk=p6.pk)
            create_page('P7', published=True, in_navigation=True, parent=p6, **defaults)
            p6 = Page.objects.get(pk=p6.pk)
            create_page('P8', published=True, in_navigation=True, parent=p6, **defaults)


class SubMenusFixture(object):
    def create_fixtures(self):
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
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',            
        }
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            p1 = create_page('P1', published=True, in_navigation=True, **defaults)
            p4 = create_page('P4', published=True, in_navigation=True, **defaults)
            p6 = create_page('P6', published=True, in_navigation=True, **defaults)
            p1 = Page.objects.get(pk=p1.pk)
            p2 = create_page('P2', published=True, in_navigation=True, parent=p1, **defaults)
            create_page('P3', published=True, in_navigation=True, parent=p2, **defaults)
            p4 = Page.objects.get(pk=p4.pk)
            create_page('P5', published=True, in_navigation=True, parent=p4, **defaults)
            p6 = Page.objects.get(pk=p6.pk)
            create_page('P7', published=True, in_navigation=False, parent=p6, **defaults)
            p6 = Page.objects.get(pk=p6.pk)
            create_page('P8', published=True, in_navigation=True, parent=p6, **defaults)


class SoftrootFixture(object):
    def create_fixtures(self):
        """
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
        
        # all in nav, published and NOT softroot
        """
        defaults = {
            'template': 'nav_playground.html',
            'language': 'en',
            'in_navigation': True,
            'published': True,
        }
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            top = create_page('top', **defaults)
            root = create_page('root', parent=top, **defaults)
            aaa = create_page('aaa', parent=root, **defaults)
            _111 = create_page('111', parent=aaa, **defaults)
            ccc = create_page('ccc', parent=_111, **defaults)
            create_page('ddd', parent=ccc, **defaults)
            aaa = Page.objects.get(pk=aaa.pk)
            create_page('222', parent=aaa, **defaults)
            root = Page.objects.get(pk=root.pk)
            bbb = create_page('bbb', parent=root, **defaults)
            create_page('333', parent=bbb, **defaults)
            bbb = Page.objects.get(pk=bbb.pk)
            create_page('444', parent=bbb, **defaults)
