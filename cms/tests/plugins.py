# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD,\
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE, \
    URL_CMS_PLUGIN_REMOVE
from cms.models import Page, Title, Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.plugins.link.models import Link
from testapp.pluginapp.models import Article, Section
from testapp.pluginapp.plugins.cms_plugins import ArticlesPlugin


class PluginsTestCase(CMSTestCase):

    def setUp(self):
        self.super_user = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        self.super_user.set_password("test")
        self.super_user.save()
        
        self.slave = User(username="slave", is_staff=True, is_active=True, is_superuser=False)
        self.slave.set_password("slave")
        self.slave.save()
        
        self.login_user(self.super_user)

# REFACTOR - the publish and appove methods exist in this file and in permmod.py - should they be in base?
    def publish_page(self, page, approve=False, user=None, published_check=True):
        if user:
            self.login_user(user)

        # publish / approve page by master
        response = self.client.post(URL_CMS_PAGE + "%d/change-status/" % page.pk, {1 :1})
        self.assertEqual(response.status_code, 200)

        if not approve:
            return self.reload_page(page)

        # approve
        page = self.approve_page(page)

        if published_check:
            # must have public object now
            assert(page.publisher_public)
            # and public object must be published
            assert(page.publisher_public.published)

        return page

    def approve_page(self, page):
        response = self.client.get(URL_CMS_PAGE + "%d/approve/" % page.pk)
        self.assertRedirects(response, URL_CMS_PAGE)
        # reload page
        return self.reload_page(page)


    def test_01_add_edit_plugin(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body":"Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)
        
    def test_02_copy_plugins(self):
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        self.assertEquals(len(settings.LANGUAGES) > 1, True)
        page = Page.objects.all()[0]
        placeholder = page.placeholders.get(slot="body")
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':placeholder.pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        text_plugin_pk = int(response.content)
        self.assertEquals(text_plugin_pk, CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        
        data = {
            "body":"Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)
        # add an inline link
        #/admin/cms/page/2799/edit-plugin/17570/add-plugin/
        #http://127.0.0.1/admin/cms/page/2799/edit-plugin/17570/edit-plugin/17574/?_popup=1
        add_url = '%s%s/add-plugin/' % (URL_CMS_PLUGIN_EDIT, text_plugin_pk)
        data = {
            'plugin_type': "LinkPlugin",
            "parent_id": txt.pk,
            "language": settings.LANGUAGES[0][0],
        }
        response = self.client.post(add_url, data)
        link_pk = response.content
        self.assertEqual(response.status_code, 200)
        # edit the inline link plugin
        edit_url = '%s%s/edit-plugin/%s/' % (URL_CMS_PLUGIN_EDIT, text_plugin_pk, link_pk)
        data = {
            'name': "A Link",
            'url': "http://www.divio.ch",
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CMSPlugin.objects.get(pk=link_pk).parent.pk, txt.pk)
        #create 2nd language page
        page_data['language'] = settings.LANGUAGES[1][0]
        page_data['title'] += " %s" % settings.LANGUAGES[1][0]
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % settings.LANGUAGES[1][0], page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        self.assertEquals(CMSPlugin.objects.all().count(), 2)
        self.assertEquals(Page.objects.all().count(), 1)
        copy_data = {
            'placeholder':page.placeholders.get(slot="body").pk,
            'language':settings.LANGUAGES[1][0],
            'copy_from':settings.LANGUAGES[0][0],
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(response.content.count('<li '), 1)
        # assert copy success
        self.assertEquals(CMSPlugin.objects.filter(language=settings.LANGUAGES[0][0]).count(), 2)
        self.assertEquals(CMSPlugin.objects.filter(language=settings.LANGUAGES[1][0]).count(), 2)
        self.assertEquals(CMSPlugin.objects.all().count(), 4)
        # assert plugin tree
        for link in CMSPlugin.objects.filter(plugin_type="LinkPlugin"):
            self.assertNotEqual(link.parent, None)
        for text in Text.objects.all():
            self.assertEquals(text.body, "Hello World")

    def test_03_remove_plugin_before_published(self):
        """
        When removing a draft plugin we would expect the public copy of the plugin to also be removed
        """
        # add a page
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # there should be only 1 plugin
        self.assertEquals(1, CMSPlugin.objects.all().count())

        # delete the plugin
        plugin_data = {
            'plugin_id': int(response.content)
        }
        remove_url = URL_CMS_PLUGIN_REMOVE
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 200)
        # there should be no plugins
        self.assertEquals(0, CMSPlugin.objects.all().count())
        
        
    def test_04_remove_plugin_after_published(self):
        # add a page
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # there should be only 1 plugin
        self.assertEquals(1, CMSPlugin.objects.all().count())
        
        # publish page
        page = self.publish_page(page)
        
        # there should now be two plugins - 1 draft, 1 public
        self.assertEquals(2, CMSPlugin.objects.all().count())
        
        # delete the plugin
        plugin_data = {
            'plugin_id': int(response.content)
        }
        remove_url = URL_CMS_PLUGIN_REMOVE
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 200)
        
        # there should be no plugins
        self.assertEquals(0, CMSPlugin.objects.all().count())
        
    def test_05_remove_plugin_after_published_under_moderation(self):
        # create content as limited rights user
        self.login_user(self.super_user)
        page = self.create_page()

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        
        # there should be only 1 plugin
        self.assertEquals(1, CMSPlugin.objects.all().count())
        
        # check publish box
        page = self.publish_page(page, published_check=False)
    
        # there should now be two plugins - 1 draft, 1 public
        self.assertEquals(2, CMSPlugin.objects.all().count())
        
        # --------------------------------------------
        #  Login as slave user and delete the plugin
        # --------------------------------------------
        self.login_user(self.super_user)
        # delete the plugin
        plugin_data = {
            'plugin_id': int(response.content)
        }
        remove_url = URL_CMS_PLUGIN_REMOVE
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 200)
        
        # there should still be 2 plugins - 1 draft, 1 public until approval
        self.assertEquals(0, CMSPlugin.objects.all().count())
        
        # login as super user and approve the page
        self.login_user(self.super_user)
        page = self.approve_page(page)
        
        # there should now be 0 plugins
        self.assertEquals(0, CMSPlugin.objects.all().count())

    def test_06_remove_plugin_not_associated_to_page(self):
        """
        Test case for PlaceholderField
        """
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder':page.placeholders.get(slot="body").pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # there should be only 1 plugin
        self.assertEquals(1, CMSPlugin.objects.all().count())
        
        ph = Placeholder(slot="subplugin")
        ph.save()
        
        plugin_data = {
            'plugin_type':"TextPlugin",
            'language':settings.LANGUAGES[0][0],
            'placeholder': ph.pk,
            'parent': int(response.content)
        }
        
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        
        plugin_data = {
            'plugin_id': int(response.content)
        }
        
        remove_url = URL_CMS_PLUGIN_REMOVE
        
        response = response.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 200)
        

class PluginManyToManyTestCase(CMSTestCase):

    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self.login_user(u)
        
        # create 3 sections
        sections = {}
        for i in range(3):
            sections[i] = Section(name="section %s" %i)
            sections[i].save()
        
        # create 10 articles by section
        for i in sections.keys():
            for j in range(10):
                article = Article(title="article %s" % j,
                                  section=sections[i])
                article.save()
         
        # Create a page       
        self.page = self.create_page()
        
        # create a plugin
        #plugin = ArticlesPlugin(plugin_type='TextPlugin', language='en',
        #              placeholder=self.page.placeholders[1], position=0,
        #              title="Articles Plugin 1",
        #              sections=sections.items())
        #plugin.insert_at(None, commit=True)

    def test_01_add_articles_plugin(self):
        import pdb; pdb.set_trace()
        self.assertEquals(True, False)
        
