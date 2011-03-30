from __future__ import with_statement
from cms.test_utils.testcases import SettingsOverrideTestCase


class ToolbarTests(SettingsOverrideTestCase):
    settings_overrides = {'CMS_MODERATOR': False}
    
    def test_01_static_html(self):
        self.assertFalse(True, "have to write toolbar tests!")