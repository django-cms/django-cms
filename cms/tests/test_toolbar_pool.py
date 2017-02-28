from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured

from cms import api
from cms.exceptions import ToolbarAlreadyRegistered, ToolbarNotRegistered
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import ToolbarPool, toolbar_pool
from cms.utils.conf import get_cms_setting


class TestToolbar(CMSToolbar):
    pass


class ToolbarPoolTests(CMSTestCase):
    def test_register(self):
        pool = ToolbarPool()
        pool.register(TestToolbar)
        pool.register(CMSToolbar)
        self.assertEqual(pool.toolbars, {
            'cms.toolbar_base.CMSToolbar': CMSToolbar,
            'cms.tests.test_toolbar_pool.TestToolbar': TestToolbar})

        self.assertRaises(ToolbarAlreadyRegistered,
                          pool.register, TestToolbar)

    def test_register_type(self):
        pool = ToolbarPool()
        self.assertRaises(ImproperlyConfigured, pool.register, str)
        self.assertRaises(ImproperlyConfigured, pool.register, object)

    def test_register_order(self):
        pool = ToolbarPool()
        pool.register(TestToolbar)
        pool.register(CMSToolbar)

        test_toolbar = OrderedDict()
        test_toolbar['cms.tests.test_toolbar_pool.TestToolbar'] = TestToolbar
        test_toolbar['cms.toolbar_base.CMSToolbar'] = CMSToolbar
        self.assertEqual(list(test_toolbar.keys()), list(pool.toolbars.keys()))

    def test_unregister(self):
        pool = ToolbarPool()
        pool.register(TestToolbar)
        pool.unregister(TestToolbar)
        self.assertEqual(pool.toolbars, {})

        self.assertRaises(ToolbarNotRegistered,
                          pool.unregister, TestToolbar)

    def test_settings(self):
        pool = ToolbarPool()
        toolbars = toolbar_pool.toolbars
        toolbar_pool.clear()
        with self.settings(CMS_TOOLBARS=['cms.cms_toolbars.BasicToolbar', 'cms.cms_toolbars.PlaceholderToolbar']):
            toolbar_pool.register(TestToolbar)
            self.assertEqual(len(list(pool.get_toolbars().keys())), 2)
            api.create_page("home", "simple.html", "en", published=True)
            with self.login_user_context(self.get_superuser()):
                response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                self.assertEqual(response.status_code, 200)
        toolbar_pool.toolbars = toolbars

    def test_watch_models(self):
        toolbar_pool.discover_toolbars()
        self.assertEqual(type(toolbar_pool.get_watch_models()), list)
