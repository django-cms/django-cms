# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

class SiteTestCase(CMSTestCase):
    """Site framework specific test cases.
    
    All stuff which is changing settings.SITE_ID for tests should come here.
    """
    def setUp(self):
        with SettingsOverride(SITE_ID=1):
            
            u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
            u.set_password("test")
            u.save()
            
            # setup sites
            self.site2 = Site.objects.create(domain="sample2.com", name="sample2.com")
            self.site3 = Site.objects.create(domain="sample3.com", name="sample3.com")
            
        self._login_context = self.login_user_context(u)
        self._login_context.__enter__()
    
    def tearDown(self):
        self._login_context.__exit__(None, None, None)
    
    
    def test_site_framework(self):
        #Test the site framework, and test if it's possible to disable it
        with SettingsOverride(SITE_ID=self.site2.pk):
            create_page("page_2a", "nav_playground.html", "en", site=self.site2)
    
            response = self.client.get("/admin/cms/page/?site__exact=%s" % self.site3.pk)
            self.assertEqual(response.status_code, 200)
            create_page("page_3b", "nav_playground.html", "en", site=self.site3)
            
        with SettingsOverride(SITE_ID=self.site3.pk):
            create_page("page_3a", "nav_playground.html", "en", site=self.site3)
            
            # with param
            self.assertEqual(Page.objects.on_site(self.site2.pk).count(), 1)
            self.assertEqual(Page.objects.on_site(self.site3.pk).count(), 2)
            
            self.assertEqual(Page.objects.drafts().on_site().count(), 2)
            
        with SettingsOverride(SITE_ID=self.site2.pk):
            # without param
            self.assertEqual(Page.objects.drafts().on_site().count(), 1)

        
