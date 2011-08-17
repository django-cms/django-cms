# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page, create_title
from cms.apphook_pool import apphook_pool
from cms.appresolver import applications_page_check, clear_app_resolvers
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.core.urlresolvers import clear_url_caches, reverse
import sys



APP_NAME = 'SampleApp'
APP_MODULE = "project.sampleapp.cms_app"


class ApphooksTestCase(CMSTestCase):

    def setUp(self):
        clear_app_resolvers()
        clear_url_caches()
        
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]

    def tearDown(self):
        clear_app_resolvers()
        clear_url_caches()

        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
    
    def test_explicit_apphooks(self):
        """
        Test explicit apphook loading with the CMS_APPHOOKS setting.
        """
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
            
            
    def test_implicit_apphooks(self):
        """
        Test implicit apphook loading with INSTALLED_APPS + cms_app.py
        """
            
        apps = ['project.sampleapp']
        with SettingsOverride(INSTALLED_APPS=apps, ROOT_URLCONF='project.urls_for_apphook_tests'):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(app_names, [APP_NAME])
            apphook_pool.clear()
    
    def test_apphook_on_root(self):
        
        with SettingsOverride(ROOT_URLCONF='project.urls_for_apphook_tests'):
            apphook_pool.clear()    
            superuser = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            page = create_page("apphooked-page", "nav_playground.html", "en",
                               created_by=superuser, published=True, apphook="SampleApp")
            blank_page = create_page("not-apphooked-page", "nav_playground.html", "en",
                                     created_by=superuser, published=True, apphook="", slug='blankapp')
            english_title = page.title_set.all()[0]
            self.assertEquals(english_title.language, 'en')
            create_title("de", "aphooked-page-de", page, apphook="SampleApp")
            self.assertTrue(page.publish())
            self.assertTrue(blank_page.publish())
    
            response = self.client.get(self.get_pages_root())
            self.assertTemplateUsed(response, 'sampleapp/home.html')

            response = self.client.get('/en/blankapp/')
            self.assertTemplateUsed(response, 'nav_playground.html')

            apphook_pool.clear()
    
    def test_get_page_for_apphook(self):
            
        with SettingsOverride(ROOT_URLCONF='project.second_urls_for_apphook_tests'):
    
            apphook_pool.clear()    
            superuser = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            page = create_page("home", "nav_playground.html", "en",
                               created_by=superuser, published=True)
            create_title('de', page.get_title(), page)
            child_page = create_page("child_page", "nav_playground.html", "en",
                         created_by=superuser, published=True, parent=page)
            create_title('de', child_page.get_title(), child_page)
            child_child_page = create_page("child_child_page", "nav_playground.html",
                "en", created_by=superuser, published=True, parent=child_page, apphook='SampleApp')
            create_title("de", child_child_page.get_title(), child_child_page, apphook='SampleApp')
            
            child_child_page.publish()
            # publisher_public is set to draft on publish, issue with onetoone reverse
            child_child_page = self.reload(child_child_page) 
            
            en_title = child_child_page.publisher_public.get_title_obj('en')

            path = reverse('en:sample-settings')
            
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'en'
            
            attached_to_page = applications_page_check(request, path=path[1:]) # strip leading slash
            self.assertEquals(attached_to_page.pk, en_title.page.pk)            
            
            response = self.client.get(path)
            self.assertEquals(response.status_code, 200)

            self.assertTemplateUsed(response, 'sampleapp/home.html')
            self.assertContains(response, en_title.title)
            
            de_title = child_child_page.publisher_public.get_title_obj('de')
            path = reverse('de:sample-settings')
        
            request = self.get_request(path)
            request.LANGUAGE_CODE = 'de'
            
            attached_to_page = applications_page_check(request, path=path[4:]) # strip leading slash and language prefix
            self.assertEquals(attached_to_page.pk, de_title.page.pk)            
            
            response = self.client.get(path)
            self.assertEquals(response.status_code, 200)
            self.assertTemplateUsed(response, 'sampleapp/home.html')
            self.assertContains(response, de_title.title)
            
            apphook_pool.clear()
