from __future__ import with_statement
from cms.test_utils.testcases import SettingsOverrideTestCase


class ToolbarTests(SettingsOverrideTestCase):
    settings_overrides = {'CMS_MODERATOR': False}