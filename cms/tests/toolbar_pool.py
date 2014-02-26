from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from cms.exceptions import ToolbarAlreadyRegistered, ToolbarNotRegistered
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import ToolbarPool


class TestToolbar(CMSToolbar):
    pass


class ToolbarPoolTests(TestCase):

    def setUp(self):
        self.pool = ToolbarPool()

    def test_register(self):
        self.pool.register(TestToolbar)
        self.pool.register(CMSToolbar)
        self.assertEqual(self.pool.toolbars, {
            'cms.toolbar_base.CMSToolbar': CMSToolbar,
            'cms.tests.toolbar_pool.TestToolbar': TestToolbar})

        self.assertRaises(ToolbarAlreadyRegistered,
                self.pool.register, TestToolbar)

    def test_register_type(self):
        self.assertRaises(ImproperlyConfigured, self.pool.register, str)
        self.assertRaises(ImproperlyConfigured, self.pool.register, object)

    def test_unregister(self):
        self.pool.register(TestToolbar)
        self.pool.unregister(TestToolbar)
        self.assertEqual(self.pool.toolbars, {})

        self.assertRaises(ToolbarNotRegistered,
                self.pool.unregister, TestToolbar)
