# -*- coding: utf-8 -*-
from cms.models import Page, Title, Placeholder
from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD
from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
import os.path


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
        self.assertEqual(response.status_code, 200)

    def test_02_create_page(self):
        """
        Test that a page can be created via the admin
        """
        page_data = self.get_new_page_data()

        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        title = Title.objects.get(slug=page_data['slug'])
        self.assertEqual(title is not None, True)
        page = title.page
        page.published = True
        page.save()
        self.assertEqual(page.get_title(), page_data['title'])
        self.assertEqual(page.get_slug(), page_data['slug'])
        self.assertEqual(page.placeholders.all().count(), 2)
        
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
            self.assertEqual(response['Location'].endswith(URL_CMS_PAGE), True)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Location'].endswith(URL_CMS_PAGE_ADD), True)
        # TODO: check for slug collisions after move
        # TODO: check for slug collisions with different settings         
  
    def test_04_details_view(self):
        """
        Test the details view
        """
        try:
            response = self.client.get(self.get_pages_root())
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise
        
        page_data = self.get_new_page_data()
        page_data['published'] = False
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        try:
            response = self.client.get(self.get_pages_root())
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise
        page_data = self.get_new_page_data()
        page_data['published'] = True
        page_data['slug'] = 'test-page-2'
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        response = self.client.get(URL_CMS_PAGE)
        
        response = self.client.get(self.get_pages_root())
        self.assertEqual(response.status_code, 200)

    def test_05_edit_page(self):
        """
        Test that a page can edited via the admin
        """
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page =  Page.objects.get(title_set__slug=page_data['slug'])
        response = self.client.get('/admin/cms/page/%s/' %page.id)
        self.assertEqual(response.status_code, 200)
        page_data['title'] = 'changed title'
        response = self.client.post('/admin/cms/page/%s/' %page.id, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        self.assertEqual(page.get_title(), 'changed title')
    
    def test_06_meta_description_and_keywords_fields_from_admin(self):
        """
        Test that description and keywords tags can be set via the admin
        """
        page_data = self.get_new_page_data()
        page_data["meta_description"] = "I am a page"
        page_data["meta_keywords"] = "page,cms,stuff"
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page =  Page.objects.get(title_set__slug=page_data['slug'])
        response = self.client.get('/admin/cms/page/%s/' %page.id)
        self.assertEqual(response.status_code, 200)
        page_data['meta_description'] = 'I am a duck'
        response = self.client.post('/admin/cms/page/%s/' %page.id, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        page = Page.objects.get(title_set__slug=page_data["slug"])
        self.assertEqual(page.get_meta_description(), 'I am a duck')
        self.assertEqual(page.get_meta_keywords(), 'page,cms,stuff')

    def test_07_meta_description_and_keywords_from_template_tags(self):
        from django import template
        page_data = self.get_new_page_data()
        page_data["title"] = "Hello"
        page_data["meta_description"] = "I am a page"
        page_data["meta_keywords"] = "page,cms,stuff"
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page =  Page.objects.get(title_set__slug=page_data['slug'])
        self.client.post('/admin/cms/page/%s/' %page.id, page_data)
        t = template.Template("{% load cms_tags %}{% page_attribute title %} {% page_attribute meta_description %} {% page_attribute meta_keywords %}")
        req = HttpRequest()
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
        
        
    def test_09_language_change(self):
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        pk = Page.objects.all()[0].pk
        response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"en" })
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"de" })
        self.assertEqual(response.status_code, 200)
        
    def test_10_move_page(self):
        page_data1 = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data1)
        page_data2 = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data2)
        page_data3 = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data3)
        page1 = Page.objects.all()[0]
        page2 = Page.objects.all()[1]
        page3 = Page.objects.all()[2]
        # move pages
        response = self.client.post("/admin/cms/page/%s/move-page/" % page3.pk, {"target":page2.pk, "position":"last-child" })
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/admin/cms/page/%s/move-page/" % page2.pk, {"target":page1.pk, "position":"last-child" })
        self.assertEqual(response.status_code, 200)
        # check page2 path and url
        page2 = Page.objects.get(pk=page2.pk)
        self.assertEqual(page2.get_path(), page_data1['slug']+"/"+page_data2['slug'])
        self.assertEqual(page2.get_absolute_url(), self.get_pages_root()+page_data1['slug']+"/"+page_data2['slug']+"/")
        # check page3 path and url
        page3 = Page.objects.get(pk=page3.pk)
        self.assertEqual(page3.get_path(), page_data1['slug']+"/"+page_data2['slug']+"/"+page_data3['slug'])
        self.assertEqual(page3.get_absolute_url(), self.get_pages_root()+page_data1['slug']+"/"+page_data2['slug']+"/"+page_data3['slug']+"/")
        # publish page 1 (becomes home)
        page1 = Page.objects.all()[0]
        page1.published = True
        page1.save()
        # check that page2 and page3 url have changed
        page2 = Page.objects.get(pk=page2.pk)
        self.assertEqual(page2.get_absolute_url(), self.get_pages_root()+page_data2['slug']+"/")
        page3 = Page.objects.get(pk=page3.pk)
        self.assertEqual(page3.get_absolute_url(), self.get_pages_root()+page_data2['slug']+"/"+page_data3['slug']+"/")
        # move page2 back to root and check path of 2 and 3
        response = self.client.post("/admin/cms/page/%s/move-page/" % page2.pk, {"target":page1.pk, "position":"left" })
        self.assertEqual(response.status_code, 200)
        page2 = Page.objects.get(pk=page2.pk)
        self.assertEqual(page2.get_path(), page_data2['slug'])
        page3 = Page.objects.get(pk=page3.pk)
        self.assertEqual(page3.get_path(), page_data2['slug']+"/"+page_data3['slug'])
        
    def test_11_add_placeholder(self):
        # create page
        page = self.create_page(None, None, "last-child", "Add Placeholder", 1, True, True)
        page.template = 'add_placeholder.html'
        page.save()
        url = page.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        path = os.path.join(settings.PROJECT_DIR, 'templates', 'add_placeholder.html')
        f = open(path, 'r')
        old = f.read()
        f.close()
        new = old.replace(
            '<!-- SECOND_PLACEHOLDER -->',
            '{% placeholder second_placeholder %}'
        )
        f = open(path, 'w')
        f.write(new)
        f.close()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        f = open(path, 'w')
        f.write(old)
        f.close()

    def test_12_sitemap_login_required_pages(self):
        """
        Test that CMSSitemap object contains only published,public (login_required=False) pages
        """
        self.create_page(parent_page=None, published=True, in_navigation=True)
        page1 = Page.objects.all()[0]
        page1.login_required = True
        page1.save()
        self.assertEqual(CMSSitemap().items().count(),0)

	
