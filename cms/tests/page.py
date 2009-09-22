# -*- coding: utf-8 -*-
from django.conf import settings
from cms.models import *
from django.test.client import Client
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from cms.tests.base import PageBaseTestCase
from cms import settings as cms_settings

class PagesTestCase(PageBaseTestCase):

    fixtures = ['test.json']
    counter = 1
    
    def setUp(self):
        u = User(username="test")
        u.set_password("test")
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True 
        u.save()
        
    
    def get_new_page_data(self):
        page_data = {'title':'test page %d' % self.counter, 
            'slug':'test-page-%d' % self.counter, 'language':'en',
            'site':1, 'published':True, 'template':'index.html'}
        
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        
        self.counter = self.counter + 1
        return page_data

    def test_01_add_page(self):
        """
        Test that the add admin page could be displayed via the admin
        """
        logged_in = self.client.login(username= 'test', password='test')
        assert logged_in
        response = self.client.get('/admin/cms/page/add/')
        assert(response.status_code == 200)

    def test_02_create_page(self):
        """
        Test that a page can be created via the admin
        """
        
        self.client.login(username= 'test', password='test')
        setattr(settings, "SITE_ID", 1)
        page_data = self.get_new_page_data()

        response = self.client.post('/admin/cms/page/add/', page_data)
        self.assertRedirects(response, '/admin/cms/page/')
        title = Title.objects.get(slug=page_data['slug'])
        assert(title is not None)
        page = title.page
        page.published = True
        page.save()
        assert(page.get_title() == page_data['title'])
        assert(page.get_slug() == page_data['slug'])
        
        # were public instanes created?
        title = Title.objects.drafts().get(slug=page_data['slug'])

        
    def test_03_slug_collision(self):
        """
        Test a slug collision
        """
        setattr(settings, "SITE_ID", 1)
        
        self.client.login(username= 'test', password='test')
        page_data = self.get_new_page_data()
        response = self.client.post('/admin/cms/page/add/', page_data)
        self.assertRedirects(response, '/admin/cms/page/')
        page1 = Title.objects.get(slug=page_data['slug']).page
        response = self.client.post('/admin/cms/page/add/', page_data)
        self.assertEqual(response.status_code, 200)
        # TODO: check for slug collisions after move
        # TODO: check for slug collisions with different settings         
  
    def test_04_details_view(self):
        """
        Test the details view
        """
        self.client.login(username= 'test', password='test')
        try:
            response = self.client.get('/')
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise

        page_data = self.get_new_page_data()
        page_data['published'] = False
        response = self.client.post('/admin/cms/page/add/', page_data)
        try:
            response = self.client.get('/')
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise

        page_data = self.get_new_page_data()
        page_data['published'] = True
        page_data['slug'] = 'test-page-2'
        response = self.client.post('/admin/cms/page/add/', page_data)
        response = self.client.get('/admin/cms/page/')
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_05_edit_page(self):
        """
        Test that a page can edited via the admin
        """
       
        self.client.login(username= 'test', password='test')
        page_data = self.get_new_page_data()
        response = self.client.post('/admin/cms/page/add/', page_data)
        response = self.client.get('/admin/cms/page/1/')
        self.assertEqual(response.status_code, 200)
        page_data['title'] = 'changed title'
        response = self.client.post('/admin/cms/page/1/', page_data)
        self.assertRedirects(response, '/admin/cms/page/')
        page = Page.objects.get(id=1)
        assert(page.get_title() == 'changed title')
    
    '''
    def test_06_site_framework(self):
        #Test the site framework, and test if it's possible to disable it
        setattr(settings, "SITE_ID", 2)
        setattr(settings, "PAGE_USE_SITE_ID", True)
        c = Client()
        c.login(username= 'batiste', password='b')
        page_data = self.get_new_page_data()
        page_data["sites"] = [2]
        response = c.post('/admin/pages/page/add/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        
        page = Title.objects.get(slug=page_data['slug']).page
        self.assertEqual(page.sites.count(), 1)
        self.assertEqual(page.sites.all()[0].id, 2)
        
        page_data = self.get_new_page_data()
        page_data["sites"] = [3]
        response = c.post('/admin/pages/page/add/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        
        # we cannot get the data posted on another site (why not after all?)
        content = Content.objects.get_content_slug_by_slug(page_data['slug'])
        self.assertEqual(content, None)
        
        setattr(settings, "SITE_ID", 3)
        page = Content.objects.get_content_slug_by_slug(page_data['slug']).page
        self.assertEqual(page.sites.count(), 1)
        self.assertEqual(page.sites.all()[0].id, 3)
        
        # with param
        self.assertEqual(Page.objects.on_site(2).count(), 1)
        self.assertEqual(Page.objects.on_site(3).count(), 1)
        
        # without param
        self.assertEqual(Page.objects.on_site().count(), 1)
        setattr(settings, "SITE_ID", 2)
        self.assertEqual(Page.objects.on_site().count(), 1)
        
        page_data = self.get_new_page_data()
        page_data["sites"] = [2, 3]
        response = c.post('/admin/pages/page/add/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        
        self.assertEqual(Page.objects.on_site(3).count(), 2)
        self.assertEqual(Page.objects.on_site(2).count(), 2)
        self.assertEqual(Page.objects.on_site().count(), 2)
        
        setattr(settings, "PAGE_USE_SITE_ID", False)
        
        # we should get everything
        self.assertEqual(Page.objects.on_site().count(), 3)
        
        self.test_02_create_page()
        self.test_05_edit_page()
        self.test_04_details_view()
    '''
    
    def test_07_meta_description_and_keywords_fields_from_admin(self):
        """
        Test that description and keywords tags can be set via the admin
        """
        self.client.login(username= 'test', password='test')
        page_data = self.get_new_page_data()
        page_data["meta_description"] = "I am a page"
        page_data["meta_keywords"] = "page,cms,stuff"
        response = self.client.post('/admin/cms/page/add/', page_data)
        response = self.client.get('/admin/cms/page/1/')
        self.assertEqual(response.status_code, 200)
        page_data['meta_description'] = 'I am a duck'
        response = self.client.post('/admin/cms/page/1/', page_data)
        self.assertRedirects(response, '/admin/cms/page/')
        page = Page.objects.get(id=1)
        assert(page.get_meta_description() == 'I am a duck')
        assert(page.get_meta_keywords() == 'page,cms,stuff')

    def test_08_meta_description_and_keywords_from_template_tags(self):
        from django import template
        self.client.login(username= 'test', password='test')
        page_data = self.get_new_page_data()
        page_data["title"] = "Hello"
        page_data["meta_description"] = "I am a page"
        page_data["meta_keywords"] = "page,cms,stuff"
        response = self.client.post('/admin/cms/page/add/', page_data)
        response = self.client.post('/admin/cms/page/1/', page_data)
        t = template.Template("{% load cms_tags %}{% page_attribute title %} {% page_attribute meta_description %} {% page_attribute meta_keywords %}")
        req = HttpRequest()
        page = Page.objects.get(id=1)
        page.published = True
        page.save()
        req.current_page = page 
        req.REQUEST = {}
        self.assertEqual(t.render(template.Context({"request": req})), "Hello I am a page page,cms,stuff")

    def test_09_copy_page(self):
        """
        Test that a page can be copied via the admin
        """
        raise "test must be reimplemented, because ids doesnt work with this system"
    
        # this case is not written properly, it must always check what was the
        # id of created page!!
        
        self.client.login(username= 'test', password='test')
        setattr(settings, "SITE_ID", 1)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/', page_data)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/?target=1&position=first-child&site=1', page_data)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/?target=2&position=first-child&site=1', page_data)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/', page_data)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/?target=4&position=first-child&site=1', page_data)
        page_data = self.get_new_page_data()
        count = Page.objects.all().count()
        response = self.client.post('/admin/cms/page/1/copy-page/', {'target':5, 'position':'first-child', 'site':1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Page.objects.all().count()>count)
        # TODO: test with m2m fields in plugins
        
    def test_10_language_change(self):
        self.client.login(username= 'test', password='test')
        setattr(settings, "SITE_ID", 1)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/', page_data)
        pk = Page.objects.all()[0].pk
        response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"en" })
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"de" })
        self.assertEqual(response.status_code, 200)
