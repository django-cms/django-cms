# -*- coding: utf-8 -*-
from cms.api import create_page
from cms.forms.widgets import PageSelectWidget, PageSmartLinkWidget
from cms.test_utils.testcases import CMSTestCase


class WidgetTestCases(CMSTestCase):
    def test_pageselectwidget(self):
        page = create_page("Test page", "nav_playground.html", "en")
        page2 = create_page("Test page2", "nav_playground.html", "en")
        widget = PageSelectWidget()
        self.assertEqual(widget.decompress(page.pk), [1, page.pk, page.pk])
        self.assertEqual(widget.decompress(page2.pk), [1, page2.pk, page2.pk])
        self.assertIn("page_1", widget.render("page", ''))
        self.assertIn("page_2", widget.render("page", ''))
        self.assertFalse(widget._has_changed([0, 1], [0, 1]))
        self.assertTrue(widget._has_changed('', [0, 1]))
        self.assertTrue(widget._has_changed([0, 1], ''))

    def test_pagesmartwidget(self):
        create_page("Test page", "nav_playground.html", "en")
        create_page("Test page2", "nav_playground.html", "en")
        widget = PageSmartLinkWidget(ajax_view='admin:cms_page_get_published_pagelist')
        widget.language = 'en'
        self.assertIn('page', widget.render("page", ''))
