from __future__ import with_statement
from cms.conf.patch import post_patch
from cms.tests.base import CMSTestCase
from cms.tests.util.context_managers import SettingsOverride


class SettingsTests(CMSTestCase):
    def test_01_dbgettext_deprecation(self):
        with SettingsOverride(CMS_DBGETTEXT_SLUGS=True):
            self.assertWarns(DeprecationWarning,
                "CMS_DBGETTEXT_SLUGS (and general support for django-dbggettext "
                "for CMS contents) will be deprecated in django CMS 2.2.",
                post_patch)