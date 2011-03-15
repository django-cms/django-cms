# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from cms.test_utils.testcases import CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_CHANGE
from cms.models import Page
from cms.plugins.text.models import Text
from cms.models.pluginmodel import CMSPlugin
from reversion.models import Revision, Version
from django.contrib.contenttypes.models import ContentType


class ReversionTestCase(CMSTestCase):
    fixtures = ['reversion_tests.json']

    def setUp(self):
        super(ReversionTestCase, self).setUp()
        self.page_data = self.get_new_page_data()

    def test_01_revert(self):
        """
        Test that you can revert a plugin
        """
        with self.login_user_context(User.objects.get(username="test")):
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
        with self.login_user_context(User.objects.get(username="test")):
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
