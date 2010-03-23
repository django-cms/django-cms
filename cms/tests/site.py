from django.conf import settings
from cms.models import Page
from cms.tests.base import CMSTestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

class SiteTestCase(CMSTestCase):
    """Site framework specific test cases.
    
    All stuff which is changing settings.SITE_ID for tests should come here.
    """
    def setUp(self):
        settings.SITE_ID = 1
        
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        # setup sites
        Site(domain="sample2.com", name="sample2.com").save() # pk 2
        Site(domain="sample3.com", name="sample3.com").save() # pk 3
        
        self.login_user(u)
    
    
    def test_01_site_framework(self):
        #Test the site framework, and test if it's possible to disable it
        settings.SITE_ID = 2
        page_2a = self.create_page(site=2)

        response = self.client.get("/admin/cms/page/?site__exact=3")
        page_3b = self.create_page(site=3)
        
        settings.SITE_ID = 3
        page_3a = self.create_page(site=3)
        
        
        # with param
        self.assertEqual(Page.objects.on_site(2).count(), 1)
        self.assertEqual(Page.objects.on_site(3).count(), 2)
        
        # without param
        settings.SITE_ID = 3
        self.assertEqual(Page.objects.drafts().on_site().count(), 2)
        
        settings.SITE_ID = 2
        self.assertEqual(Page.objects.drafts().on_site().count(), 1)
        
        settings.SITE_ID = 1
        