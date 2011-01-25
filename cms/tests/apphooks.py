# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.apphook_pool import apphook_pool
from cms.appresolver import applications_page_check, clear_app_resolvers

from cms.models.titlemodels import Title
from cms.test.testcases import CMSTestCase
from cms.test.util.context_managers import SettingsOverride
from django.contrib.auth.models import User
from django.core.urlresolvers import clear_url_caches, reverse
import sys


APP_NAME = 'SampleApp'
APP_MODULE = "testapp.sampleapp.cms_app"


class ApphooksTestCase(CMSTestCase):

    def setUp(self):
        clear_app_resolvers()
        clear_url_caches()
    
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
        with SettingsOverride(INSTALLED_APPS=apps, ROOT_URLCONF='testapp.urls_for_apphook_tests'):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(app_names, [APP_NAME])
            apphook_pool.clear()
    
    def test_03_apphook_on_root(self):
        
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
            
        with SettingsOverride(ROOT_URLCONF='testapp.urls_for_apphook_tests'):
            apphook_pool.clear()    
            superuser = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            page = self.create_page(user=superuser, published=True)
            english_title = page.title_set.all()[0]
            self.assertEquals(english_title.language, 'en')
            Title.objects.create(
                language='de',
                title='%s DE' % english_title.title,
                slug=english_title.slug,
                path=english_title.path,
                page=page,
            )
            page.title_set.all().update(application_urls='SampleApp')
            self.assertTrue(page.publish())
    
            response = self.client.get(self.get_pages_root())
            self.assertTemplateUsed(response, 'sampleapp/home.html')
            apphook_pool.clear()
    
    def test_04_get_page_for_apphook(self):
        
        if APP_MODULE in sys.modules:
            del sys.modules[APP_MODULE]
            
        with SettingsOverride(ROOT_URLCONF='testapp.second_urls_for_apphook_tests'):
    
            apphook_pool.clear()    
            superuser = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            page = self.create_page(user=superuser, published=True)
            self.create_title(page.get_title(), page.get_slug(), 'de', page)
            child_page = self.create_page(page, user=superuser, published=True)
            self.create_title(child_page.get_title(), child_page.get_slug(), 'de', child_page)
            child_child_page = self.create_page(child_page, user=superuser, published=True)
            self.create_title(child_child_page.get_title(), child_child_page.get_slug(), 'de', child_child_page)
            child_child_page.title_set.all().update(application_urls='SampleApp')
            
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