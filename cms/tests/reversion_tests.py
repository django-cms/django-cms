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
from reversion.models import Revision, Version
from django.contrib.contenttypes.models import ContentType


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
        placeholderpk = page.placeholders.get(slot="body").pk
        plugin_data = {
            'plugin_type':"TextPlugin",
            'page_id':page.pk,
            'language':settings.LANGUAGES[0][0],
            'placeholder':placeholderpk,
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
        p_data = self.page_data.copy()
        p_data['published'] = True
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, p_data)
        self.assertRedirects(response, URL_CMS_PAGE)
    
    def test_01_revert(self):
        """
        Test that you can revert a plugin
        """
        self.assertEquals(Page.objects.all().count(), 2)
        self.assertEquals(CMSPlugin.objects.all().count(), 2)
        self.assertEquals(Revision.objects.all().count(), 5)
        ctype = ContentType.objects.get_for_model(Page)
        revision = Revision.objects.all()[2]
        version = Version.objects.get(content_type=ctype, revision=revision)
        page = Page.objects.all()[0]
        history_url = URL_CMS_PAGE_CHANGE % (page.pk) + "history/"
        response = self.client.get(history_url)
        self.assertEquals(response.status_code, 200)
        revert_url = history_url + "%s/" % version.pk
        response = self.client.get(revert_url)
        self.assertEquals(response.status_code, 200)
        response = self.client.post(revert_url, self.page_data)
        self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page.pk)
        # test for publisher_is_draft, published is set for both draft and published page
        self.assertEquals(Page.objects.all()[0].publisher_is_draft, True)
        self.assertEquals(CMSPlugin.objects.all().count(), 2)
        # test that CMSPlugin subclasses are reverted
        self.assertEquals(Text.objects.all().count(), 2)
        self.assertEquals(Revision.objects.all().count(), 6)
    
    def test_02_recover(self):
        """
        Test that you can recover a page
        """
        self.assertEquals(Revision.objects.all().count(), 5)
        ctype = ContentType.objects.get_for_model(Page)
        revision = Revision.objects.all()[4]
        version = Version.objects.get(content_type=ctype, revision=revision)
        
        self.assertEquals(Page.objects.all().count(), 2)
        self.assertEquals(CMSPlugin.objects.all().count(), 2)
        self.assertEquals(Text.objects.all().count(), 2)
        
        page = Page.objects.all()[0]
        page_pk = page.pk
        page.delete_with_public()
        
        self.assertEquals(Page.objects.all().count(), 0)
        self.assertEquals(CMSPlugin.objects.all().count(), 0)
        self.assertEquals(Text.objects.all().count(), 0)
                
        recover_url = URL_CMS_PAGE + "recover/"
        response = self.client.get(recover_url)
        self.assertEquals(response.status_code, 200)
        recover_url += "%s/" % version.pk
        response = self.client.get(recover_url)
        self.assertEquals(response.status_code, 200)
        response = self.client.post(recover_url, self.page_data)
        self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page_pk)
        self.assertEquals(Page.objects.all().count(), 1)
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        # test that CMSPlugin subclasses are recovered
        self.assertEquals(Text.objects.all().count(), 1)