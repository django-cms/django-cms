# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.admin.forms import PageForm
from cms.api import create_page
from cms.models import Page, Title
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.sitemaps import CMSSitemap
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE, 
    URL_CMS_PAGE_ADD)
from cms.test_utils.util.context_managers import (LanguageOverride, 
    SettingsOverride)
from cms.utils.page_resolver import get_page_from_request
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
import datetime
import os.path

class PagesTestCase(CMSTestCase):
    
    def test_add_page(self):
        """
        Test that the add admin page could be displayed via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 200)

    def test_create_page(self):
        """
        Test that a page can be created via the admin
        """
        page_data = self.get_new_page_data()

        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            title = Title.objects.get(slug=page_data['slug'])
            self.assertNotEqual(title, None)
            page = title.page
            page.published = True
            page.save()
            self.assertEqual(page.get_title(), page_data['title'])
            self.assertEqual(page.get_slug(), page_data['slug'])
            self.assertEqual(page.placeholders.all().count(), 2)
            
            # were public instanes created?
            title = Title.objects.drafts().get(slug=page_data['slug'])

        
    def test_slug_collision(self):
        """
        Test a slug collision
        """
        page_data = self.get_new_page_data()
        # create first page
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
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
  
    def test_details_view(self):
        """
        Test the details view
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(self.get_pages_root())
            self.assertEqual(response.status_code, 404)
            page = create_page('test page 1', "nav_playground.html", "en")
            response = self.client.get(self.get_pages_root())
            self.assertEqual(response.status_code, 404)
            self.assertTrue(page.publish())
            create_page("test page 2", "nav_playground.html", "en", 
                                           parent=page, published=True)
            homepage = Page.objects.get_home()
            self.assertTrue(homepage.get_slug(), 'test-page-1')
            response = self.client.get(self.get_pages_root())
            self.assertEqual(response.status_code, 200)

    def test_edit_page(self):
        """
        Test that a page can edited via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            page =  Page.objects.get(title_set__slug=page_data['slug'])
            response = self.client.get('/admin/cms/page/%s/' %page.id)
            self.assertEqual(response.status_code, 200)
            page_data['title'] = 'changed title'
            response = self.client.post('/admin/cms/page/%s/' %page.id, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertEqual(page.get_title(), 'changed title')
    
    def test_meta_description_and_keywords_fields_from_admin(self):
        """
        Test that description and keywords tags can be set via the admin
        """
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
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

    def test_meta_description_and_keywords_from_template_tags(self):
        from django import template
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
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
    
    
    def test_copy_page(self):
        """
        Test that a page can be copied via the admin
        """
        page_a = create_page("page_a", "nav_playground.html", "en")
        page_a_a = create_page("page_a_a", "nav_playground.html", "en",
                                    parent=page_a)
        create_page("page_a_a_a", "nav_playground.html", "en", parent=page_a_a)
        
        page_b = create_page("page_b", "nav_playground.html", "en")
        page_b_a = create_page("page_b", "nav_playground.html", "en", 
                                    parent=page_b)
        
        count = Page.objects.drafts().count()
        
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            self.copy_page(page_a, page_b_a)
        
        self.assertEqual(Page.objects.drafts().count() - count, 3)
        
        
    def test_language_change(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            pk = Page.objects.all()[0].pk
            response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"en" })
            self.assertEqual(response.status_code, 200)
            response = self.client.get("/admin/cms/page/%s/" % pk, {"language":"de" })
            self.assertEqual(response.status_code, 200)
        
    def test_move_page(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
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
            response = self.client.post("/admin/cms/page/%s/move-page/" % page3.pk, {"target": page2.pk, "position": "last-child"})
            self.assertEqual(response.status_code, 200)
            response = self.client.post("/admin/cms/page/%s/move-page/" % page2.pk, {"target": page1.pk, "position": "last-child"})
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
            page1 = Page.objects.get(pk=page1.pk)
            page1.publish()
            public_page1 = page1.publisher_public
            self.assertEqual(public_page1.get_path(), '')
            # check that page2 and page3 url have changed
            page2 = Page.objects.get(pk=page2.pk)
            page2.publish()
            public_page2 = page2.publisher_public
            self.assertEqual(public_page2.get_absolute_url(), self.get_pages_root()+page_data2['slug']+"/")
            page3 = Page.objects.get(pk=page3.pk)
            page3.publish()
            public_page3 = page3.publisher_public
            self.assertEqual(public_page3.get_absolute_url(), self.get_pages_root()+page_data2['slug']+"/"+page_data3['slug']+"/")
            # move page2 back to root and check path of 2 and 3
            response = self.client.post("/admin/cms/page/%s/move-page/" % page2.pk, {"target": page1.pk, "position": "right"})
            self.assertEqual(response.status_code, 200)
            page1 = Page.objects.get(pk=page1.pk)
            self.assertEqual(page1.get_path(), page_data1['slug'])
            page2 = Page.objects.get(pk=page2.pk)
            self.assertEqual(page2.get_path(), page_data2['slug'])
            page3 = Page.objects.get(pk=page3.pk)
            self.assertEqual(page3.get_path(), page_data2['slug']+"/"+page_data3['slug'])
        
    def test_move_page_inherit(self):
        parent = create_page("Parent", 'col_three.html', "en")
        child = create_page("Child", settings.CMS_TEMPLATE_INHERITANCE_MAGIC,
                            "en", parent=parent)
        self.assertEqual(child.get_template(), parent.get_template())
        child.move_page(parent, 'left')
        self.assertEqual(child.get_template(), parent.get_template())
        
        
    def test_add_placeholder(self):
        # create page
        page = create_page("Add Placeholder", "nav_playground.html", "en",
                           position="last-child", published=True, in_navigation=True)
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

    def test_sitemap_login_required_pages(self):
        """
        Test that CMSSitemap object contains only published,public (login_required=False) pages
        """
        create_page("page", "nav_playground.html", "en", login_required=True,
                    published=True, in_navigation=True)
        self.assertEqual(CMSSitemap().items().count(),0)

    def test_edit_page_other_site_and_language(self):
        """
        Test that a page can edited via the admin when your current site is
        different from the site you are editing and the language isn't available
        for the current site.
        """
        site = Site.objects.create(domain='otherlang', name='otherlang')
        # Change site for this session
        page_data = self.get_new_page_data()
        page_data['site'] = site.pk
        page_data['title'] = 'changed title'
        TESTLANG = settings.CMS_SITE_LANGUAGES[site.pk][0]
        page_data['language'] = TESTLANG
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            page =  Page.objects.get(title_set__slug=page_data['slug'])
            with LanguageOverride(TESTLANG):
                self.assertEqual(page.get_title(), 'changed title')
        
    def test_flat_urls(self):
        with SettingsOverride(CMS_FLAT_URLS=True):
            home_slug = "home"
            child_slug = "child"
            grandchild_slug = "grandchild"
            home = create_page(home_slug, "nav_playground.html", "en",
                               published=True, in_navigation=True)
            home.publish()
            child = create_page(child_slug, "nav_playground.html", "en",
                                parent=home, published=True, in_navigation=True)
            child.publish()
            grandchild = create_page(grandchild_slug, "nav_playground.html", "en",
                                     parent=child, published=True, in_navigation=True)
            grandchild.publish()
            response = self.client.get(home.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            response = self.client.get(child.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            response = self.client.get(grandchild.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            self.assertFalse(child.get_absolute_url() in grandchild.get_absolute_url())

    def test_templates(self):
        """
        Test the inheritance magic for templates
        """
        parent = create_page("parent", "nav_playground.html", "en")
        child = create_page("child", "nav_playground.html", "en", parent=parent)
        child.template = settings.CMS_TEMPLATE_INHERITANCE_MAGIC
        child.save()
        self.assertEqual(child.template, settings.CMS_TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(parent.get_template_name(), child.get_template_name())
        parent.template = settings.CMS_TEMPLATE_INHERITANCE_MAGIC
        parent.save()
        self.assertEqual(parent.template, settings.CMS_TEMPLATE_INHERITANCE_MAGIC)
        self.assertEqual(parent.get_template(), settings.CMS_TEMPLATES[0][0])
        self.assertEqual(parent.get_template_name(), settings.CMS_TEMPLATES[0][1])
        
    def test_delete_with_plugins(self):
        """
        Check that plugins and placeholders get correctly deleted when we delete
        a page!
        """
        page = create_page("page", "nav_playground.html", "en")
        page.rescan_placeholders() # create placeholders
        placeholder = page.placeholders.all()[0]
        plugin_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder, 
            position=1, 
            language=settings.LANGUAGES[0][0]
        )
        plugin_base.insert_at(None, position='last-child', save=False)
                
        plugin = Text(body='')
        plugin_base.set_base_attr(plugin)
        plugin.save()
        self.assertEqual(CMSPlugin.objects.count(), 1)
        self.assertEqual(Text.objects.count(), 1)
        self.assertTrue(Placeholder.objects.count()  > 0)
        page.delete()
        self.assertEqual(CMSPlugin.objects.count(), 0)
        self.assertEqual(Text.objects.count(), 0)
        self.assertEqual(Placeholder.objects.count(), 0)
        
    def test_get_page_from_request_on_non_cms_admin(self):
        request = self.get_request(
            reverse('admin:sampleapp_category_change', args=(1,))
        )
        page = get_page_from_request(request)
        self.assertEqual(page, None)
        
    def test_get_page_from_request_on_cms_admin(self):
        page = create_page("page", "nav_playground.html", "en")
        request = self.get_request(
            reverse('admin:cms_page_change', args=(page.pk,))
        )
        found_page = get_page_from_request(request)
        self.assertTrue(found_page)
        self.assertEqual(found_page.pk, page.pk)
        
    def test_get_page_from_request_on_cms_admin_nopage(self):
        request = self.get_request(
            reverse('admin:cms_page_change', args=(1,))
        )
        page = get_page_from_request(request)
        self.assertEqual(page, None)
        
    def test_get_page_from_request_cached(self):
        mock_page = 'hello world'
        request = self.get_request(
            reverse('admin:sampleapp_category_change', args=(1,))
        )
        request._current_page_cache = mock_page
        page = get_page_from_request(request)
        self.assertEqual(page, mock_page)
        
    def test_get_page_from_request_nopage(self):
        request = self.get_request('/')
        page = get_page_from_request(request)
        self.assertEqual(page, None)
    
    def test_get_page_from_request_with_page_404(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        page.publish()
        request = self.get_request('/does-not-exist/')
        found_page = get_page_from_request(request)
        self.assertEqual(found_page, None)
    
    def test_get_page_from_request_with_page_preview(self):
        page = create_page("page", "nav_playground.html", "en")
        request = self.get_request('%s?preview' % page.get_absolute_url())
        request.user.is_staff = False
        found_page = get_page_from_request(request)
        self.assertEqual(found_page, None)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            request = self.get_request('%s?preview&draft' % page.get_absolute_url())
            found_page = get_page_from_request(request)
            self.assertTrue(found_page)
            self.assertEqual(found_page.pk, page.pk)
        
    def test_get_page_from_request_on_cms_admin_with_editplugin(self):
        page = create_page("page", "nav_playground.html", "en")
        request = self.get_request(
            reverse('admin:cms_page_change', args=(page.pk,)) + 'edit-plugin/42/'
        )
        found_page = get_page_from_request(request)
        self.assertTrue(found_page)
        self.assertEqual(found_page.pk, page.pk)
        
    def test_get_page_from_request_on_cms_admin_with_editplugin_nopage(self):
        request = self.get_request(
            reverse('admin:cms_page_change', args=(1,)) + 'edit-plugin/42/'
        )
        page = get_page_from_request(request)
        self.assertEqual(page, None)
    
    def test_page_already_expired(self):
        """
        Test that a page which has a end date in the past gives a 404, not a
        500.
        """
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            page = create_page('page', 'nav_playground.html', 'en',
                               publication_end_date=yesterday, published=True)
            resp = self.client.get(page.get_absolute_url('en'))
            self.assertEqual(resp.status_code, 404)
    
    def test_existing_overwrite_url(self):
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            create_page('home', 'nav_playground.html', 'en', published=True)
            create_page('boo', 'nav_playground.html', 'en', published=True)
            data = {
                'title': 'foo',
                'overwrite_url': '/boo/',
                'slug': 'foo',
                'language': 'en',
                'template': 'nav_playground.html',
                'site': 1,
            }
            form = PageForm(data)
            self.assertFalse(form.is_valid())
            self.assertTrue('overwrite_url' in form.errors)
        
    def test_page_urls(self):
        page1 = create_page('test page 1', 'nav_playground.html', 'en',
            published=True)

        page2 = create_page('test page 2', 'nav_playground.html', 'en',
            published=True, parent=page1)

        page3 = create_page('test page 3', 'nav_playground.html', 'en',
            published=True, parent=page2)

        page4 = create_page('test page 4', 'nav_playground.html', 'en',
            published=True)

        page5 = create_page('test page 5', 'nav_playground.html', 'en',
            published=True, parent=page4)

        self.assertEqual(page1.get_absolute_url(),
            self.get_pages_root()+'')
        self.assertEqual(page2.get_absolute_url(),
            self.get_pages_root()+'test-page-2/')
        self.assertEqual(page3.get_absolute_url(),
            self.get_pages_root()+'test-page-2/test-page-3/')
        self.assertEqual(page4.get_absolute_url(),
            self.get_pages_root()+'test-page-4/')
        self.assertEqual(page5.get_absolute_url(),
            self.get_pages_root()+'test-page-4/test-page-5/')

        page3 = self.move_page(page3, page1)
        self.assertEqual(page3.get_absolute_url(),
            self.get_pages_root()+'test-page-3/')

        page5 = self.move_page(page5, page2)
        self.assertEqual(page5.get_absolute_url(),
            self.get_pages_root()+'test-page-2/test-page-5/')

        page3 = self.move_page(page3, page4)
        self.assertEqual(page3.get_absolute_url(),
            self.get_pages_root()+'test-page-4/test-page-3/')
    
    def test_home_slug_not_accessible(self):
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            page = create_page('page', 'nav_playground.html', 'en', published=True)
            self.assertEqual(page.get_absolute_url('en'), '/')
            resp = self.client.get('/en/')
            self.assertEqual(resp.status_code, HttpResponse.status_code)
            resp = self.client.get('/en/page/')
            self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

    def test_public_home_page_replaced(self):
        """Test that publishing changes to the home page doesn't move the public version"""
        home = create_page('home', 'nav_playground.html', 'en', published = True, slug = 'home')
        self.assertEqual(Page.objects.drafts().get_home().get_slug(), 'home')
        home.publish()
        self.assertEqual(Page.objects.public().get_home().get_slug(), 'home')
        other = create_page('other', 'nav_playground.html', 'en', published = True, slug = 'other')
        other.publish()
        self.assertEqual(Page.objects.drafts().get_home().get_slug(), 'home')
        self.assertEqual(Page.objects.public().get_home().get_slug(), 'home')
        home = Page.objects.get(pk = home.id)
        home.in_navigation = True
        home.save()
        home.publish()
        self.assertEqual(Page.objects.drafts().get_home().get_slug(), 'home')
        self.assertEqual(Page.objects.public().get_home().get_slug(), 'home')

class NoAdminPageTests(CMSTestCase):
    urls = 'project.noadmin_urls'
    
    def setUp(self):
        admin = 'django.contrib.admin'
        noadmin_apps = [app for app in settings.INSTALLED_APPS if not app == admin]
        self._ctx = SettingsOverride(INSTALLED_APPS=noadmin_apps)
        self._ctx.__enter__()
        
    def tearDown(self):
        self._ctx.__exit__(None, None, None)
    
    def test_get_page_from_request_fakeadmin_nopage(self):
        request = self.get_request('/admin/')
        page = get_page_from_request(request)
        self.assertEqual(page, None)

class PreviousFilteredSiblingsTests(CMSTestCase):
    def test_with_publisher(self):
        home = create_page('home', 'nav_playground.html', 'en', published=True)
        home.publish()
        other = create_page('other', 'nav_playground.html', 'en', published=True)
        other.publish()
        other = Page.objects.get(pk=other.pk)
        home = Page.objects.get(pk=home.pk)
        self.assertEqual(other.get_previous_filtered_sibling(), home)
        self.assertEqual(home.get_previous_filtered_sibling(), None)
        
    def test_multisite(self):
        firstsite = Site.objects.create(name='first', domain='first.com')
        secondsite = Site.objects.create(name='second', domain='second.com')
        home = create_page('home', 'nav_playground.html', 'en', published=True, site=firstsite)
        home.publish()
        other = create_page('other', 'nav_playground.html', 'en', published=True, site=secondsite)
        other.publish()
        other = Page.objects.get(pk=other.pk)
        home = Page.objects.get(pk=home.pk)
        self.assertEqual(other.get_previous_filtered_sibling(), None)
        self.assertEqual(home.get_previous_filtered_sibling(), None)
        
