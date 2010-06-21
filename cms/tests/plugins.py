# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD,\
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE
from cms.models import Page, Title
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.plugins.link.models import Link


class PluginsTestCase(CMSTestCase):

    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self.login_user(u)
    
    def test_01_add_edit_plugin(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
#        self.assertRedirects(response, URL_CMS_PAGE)
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
        
        