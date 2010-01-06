# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD,\
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE
from cms.models import Page, Title
from cms.plugins.text.models import Text
from cms.models.pluginmodel import CMSPlugin
from reversion.models import Revision


class ReversionTestCase(CMSTestCase):

    def setUp(self):
        u = User(username="test", is_staff = True, is_active = True, is_superuser = True)
        u.set_password("test")
        u.save()
        
        self.login_user(u)
        # add a new text plugin
        self.page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, self.page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type':"TextPlugin",
            'page_id':page.pk,
            'language':settings.LANGUAGES[0][0],
            'placeholder':"body",
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(int(response.content), CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + response.content + "/"
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        response = self.client.post(edit_url, {"body":"Hello World"})
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)
        # change the content
        response = self.client.post(edit_url, {"body":"Bye Bye World"})
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Bye Bye World", txt.body)
        
        
    
    def test_01_revert(self):
        """
        Test that you can revert a plugin
        """
        self.assertEquals(Page.objects.all().count(), 1)
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        page = Page.objects.all()[0]
        self.assertEquals(Revision.objects.all().count(), 4)
        revision = Revision.objects.all()[2]
        history_url = URL_CMS_PAGE_CHANGE % (page.pk) + "history/"
        response = self.client.get(history_url)
        self.assertEquals(response.status_code, 200)
        revert_url = history_url + "%s/" % revision.pk
        response = self.client.get(revert_url)
        self.assertEquals(response.status_code, 200)
        response = self.client.post(revert_url, self.page_data)
        self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page.pk)
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        plugin = Text.objects.all()[0]
        self.assertEquals(plugin.body, "Hello World")
        
        
    
    def test_02_recover(self):
        """
        Test that the add admin page could be displayed via the admin
        """
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, 200)
