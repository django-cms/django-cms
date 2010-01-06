# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.contrib.auth.models import User
from cms.tests.base import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD,\
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT
from cms.models import Page, Title
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text


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
        data = {
            "body":"Hello World"
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)