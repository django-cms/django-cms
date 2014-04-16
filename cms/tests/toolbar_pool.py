from cms.utils.conf import get_cms_setting
from cms import api
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import SortedDict

from cms.exceptions import ToolbarAlreadyRegistered, ToolbarNotRegistered
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import ToolbarPool, toolbar_pool


class TestToolbar(CMSToolbar):
    pass


class ToolbarPoolTests(CMSTestCase):

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

    def test_register_order(self):
        self.pool.register(TestToolbar)
        self.pool.register(CMSToolbar)

        test_toolbar = SortedDict()
        test_toolbar['cms.tests.toolbar_pool.TestToolbar'] = TestToolbar
        test_toolbar['cms.toolbar_base.CMSToolbar'] = CMSToolbar
        self.assertEqual(list(test_toolbar.keys()), list(self.pool.toolbars.keys()))

    def test_unregister(self):
        self.pool.register(TestToolbar)
        self.pool.unregister(TestToolbar)
        self.assertEqual(self.pool.toolbars, {})

        self.assertRaises(ToolbarNotRegistered,
                          self.pool.unregister, TestToolbar)

    def test_settings(self):
        toolbars = toolbar_pool.toolbars
        toolbar_pool.clear()
        with SettingsOverride(CMS_TOOLBARS=['cms.cms_toolbar.BasicToolbar', 'cms.cms_toolbar.PlaceholderToolbar']):
            toolbar_pool.register(TestToolbar)
            self.assertEqual(len(list(self.pool.get_toolbars().keys())), 2)
            api.create_page("home", "simple.html", "en", published=True)
            with self.login_user_context(self.get_superuser()):
                response = self.client.get("/en/?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                self.assertEqual(response.status_code, 200)
        toolbar_pool.toolbars = toolbars

