# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD
from cms.models import Page, Title


class PagesTestCase(CMSTestCase):

    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self.login_user(u)
    
    def test_01_add_page(self):
        """
        Test that the add admin page could be displayed via the admin
        """
        response = self.client.get(URL_CMS_PAGE_ADD)
        assert(response.status_code == 200)

    def test_02_create_page(self):
        """
        Test that a page can be created via the admin
        """
        page_data = self.get_new_page_data()

        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
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
        page_data = self.get_new_page_data()
        # create first page
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        #page1 = Title.objects.get(slug=page_data['slug']).page
        # create page with the same page_data
        
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        
        if settings.i18n_installed:
            self.assertEqual(response.status_code, 302)
            # did we got right redirect?
            assert(response['Location'].endswith(URL_CMS_PAGE))
        else:
            self.assertEqual(response.status_code, 200)
            assert(response['Location'].endswith(URL_CMS_PAGE_ADD))
        # TODO: check for slug collisions after move
        # TODO: check for slug collisions with different settings         
  
    def test_04_details_view(self):
        """
        Test the details view
        """
        try:
            response = self.client.get('/')
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise

        page_data = self.get_new_page_data()
        page_data['published'] = False
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        try:
            response = self.client.get('/')
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise

        page_data = self.get_new_page_data()
        page_data['published'] = True
        page_data['slug'] = 'test-page-2'
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        response = self.client.get(URL_CMS_PAGE)
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_05_edit_page(self):
        """
        Test that a page can edited via the admin
        """
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        response = self.client.get('/admin/cms/page/1/')
        self.assertEqual(response.status_code, 200)
        page_data['title'] = 'changed title'
        response = self.client.post('/admin/cms/page/1/', page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        page = Page.objects.get(id=1)
        assert(page.get_title() == 'changed title')
    
    def test_06_meta_description_and_keywords_fields_from_admin(self):
        """
        Test that description and keywords tags can be set via the admin
        """
        page_data = self.get_new_page_data()
        page_data["meta_description"] = "I am a page"
        page_data["meta_keywords"] = "page,cms,stuff"
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        response = self.client.get('/admin/cms/page/1/')
        self.assertEqual(response.status_code, 200)
        page_data['meta_description'] = 'I am a duck'
        response = self.client.post('/admin/cms/page/1/', page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        page = Page.objects.get(id=1)
        assert(page.get_meta_description() == 'I am a duck')
        assert(page.get_meta_keywords() == 'page,cms,stuff')

    def test_07_meta_description_and_keywords_from_template_tags(self):
        from django import template
        page_data = self.get_new_page_data()
        page_data["title"] = "Hello"
        page_data["meta_description"] = "I am a page"
        page_data["meta_keywords"] = "page,cms,stuff"
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.client.post('/admin/cms/page/1/', page_data)
        t = template.Template("{% load cms_tags %}{% page_attribute title %} {% page_attribute meta_description %} {% page_attribute meta_keywords %}")
        req = HttpRequest()
        page = Page.objects.get(id=1)
        page.published = True
        page.save()
        req.current_page = page 
        req.REQUEST = {}
        self.assertEqual(t.render(template.Context({"request": req})), "Hello I am a page page,cms,stuff")
    
    
    def test_08_copy_page(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = self.create_page()
        page_a_a = self.create_page(page_a)
        page_a_a_a = self.create_page(page_a_a)
        
        page_b = self.create_page()
        page_b_a = self.create_page(page_b)
        
        count = Page.objects.drafts().count()
        
        self.copy_page(page_a, page_b_a)
        
        self.assertEqual(Page.objects.drafts().count() - count, 3)
        
        
    def test_9_language_change(self):
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        pk = Page.objects.all()[0].pk
        response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"en" })
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"de" })
        self.assertEqual(response.status_code, 200)
        
    """
    This is not a valid test, please write correct tests, which work, this must
    create at lest 2 language mutations of page before delete
    
    def test_11_language_delete(self):
        self.client.login(username= 'test', password='test')
        setattr(settings, "SITE_ID", 1)
        page_data = self.get_new_page_data()
        self.client.post('/admin/cms/page/add/', page_data)
        pk = Page.objects.all()[0].pk
        response = self.client.get("/admin/cms/page/%s/delete-translation/" % pk, {"language":"en" })
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/admin/cms/page/%s/delete-translation/" % pk, {"language":"en" })
        self.assertEqual(response.status_code, 302)
    """