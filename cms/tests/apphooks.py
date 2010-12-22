'''
Created on Dec 10, 2010

@author: jonas
'''
from __future__ import with_statement
from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_patterns
from cms.tests.base import CMSTestCase
from cms.tests.util.settings_contextmanager import SettingsOverride
from django.contrib.auth.models import User
from django.core.urlresolvers import clear_url_caches
import sys


APP_NAME = 'SampleApp'
APP_MODULE = "testapp.sampleapp.cms_app"


class ApphooksTestCase(CMSTestCase):
    def test_01_explicit_apphooks(self):
        """
        Test explicit apphook loading with the CMS_APPHOOKS setting.
        """
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
        apphooks = (
            '%s.%s' % (APP_MODULE, APP_NAME),
        )
        with SettingsOverride(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(app_names, [APP_NAME])
            apphook_pool.clear()
            
            
    def test_02_implicit_apphooks(self):
        """
        Test implicit apphook loading with INSTALLED_APPS + cms_app.py
        """
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
            
        apps = ['testapp.sampleapp']
        with SettingsOverride(INSTALLED_APPS=apps):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(app_names, [APP_NAME])
            apphook_pool.clear()
    
    def test_03_apphook_on_root(self):
        
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
            
        apphook_pool.clear()    
        superuser = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
        page = self.new_create_page(user=superuser, published=True)
        page.title_set.all().update(application_urls='SampleApp')
        self.assertEquals(page.title_set.all()[0].language, 'en')
        self.assertTrue(page.publish())

        response = self.client.get(self.get_pages_root())
        self.assertTemplateUsed(response, 'sampleapp/home.html')
        apphook_pool.clear()
