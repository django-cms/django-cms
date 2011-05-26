# -*- coding: utf-8 -*-
from __future__ import with_statement
from StringIO import StringIO
from cms.api import create_page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.api import create_page
from django.core.management import call_command
from django.core.management.base import CommandError
from cms.models.titlemodels import Title

APPHOOK = 'SampleApp'

class ManagementTestCase(CMSTestCase):
    
    def test_no_apphook(self):
        out = StringIO()
        call_command('cms', APPHOOK, uninstall_apphooks=True, interactive=False, stout=out)
        self.assertEqual(out.getvalue(), "")

    def test_with_apphook(self):
        out = StringIO()
        apps = ['cms', 'menus', 'sekizai', 'project.sampleapp']
        with SettingsOverride(INSTALLED_APPS=apps):
            create_page("Hello Title", 'nav_playground.html', 'en', apphook=APPHOOK)
            self.assertEqual(Title.objects.filter(application_urls=APPHOOK).count(), 1)            
            call_command('cms', APPHOOK,  uninstall_apphooks=True, interactive=False, stout=out)
            self.assertEqual(out.getvalue(), "")
            self.assertEqual(Title.objects.filter(application_urls=APPHOOK).count(), 0)
