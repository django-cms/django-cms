# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.models import Page
from cms.models.pluginmodel import CMSPlugin
from cms.plugins.text.models import Text
from cms.test_utils.testcases import (CMSTestCase, URL_CMS_PAGE,
    URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_ADD,
    URL_CMS_PLUGIN_EDIT)
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from os.path import join
from project.fileapp.models import FileModel
from reversion.models import Revision, Version
from reversion import revision as revision_manager
import shutil

class ReversionTestCase(CMSTestCase):
    def setUp(self):
        u = User(username="test", is_staff=True, is_active=True,
            is_superuser=True)
        u.set_password("test")
        u.save()

        with self.login_user_context(u):
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
            self.assertEquals(int(response.content),
                CMSPlugin.objects.all()[0].pk)

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

    def test_revert(self):
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

            # test for publisher_is_draft, published is set for both draft and
            # published page
            self.assertEquals(Page.objects.all()[0].publisher_is_draft, True)
            self.assertEquals(CMSPlugin.objects.all().count(), 2)

            # test that CMSPlugin subclasses are reverted
            self.assertEquals(Text.objects.all().count(), 2)
            self.assertEquals(Revision.objects.all().count(), 6)

    def test_recover(self):
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

class ReversionFileFieldTests(CMSTestCase):
    def tearDown(self):
        shutil.rmtree(join(settings.MEDIA_ROOT, 'fileapp'))

    def test_file_persistence(self):
        with revision_manager:
            # add a file instance
            file1 = FileModel()
            file1.test_file.save('file1.txt',
                SimpleUploadedFile('file1.txt', 'content1'), False)
            file1.save()
            # manually add a revision because we use the explicit way
            # django-cms uses too.
            revision_manager.add(file1)

        # reload the instance from db
        file2 = FileModel.objects.all()[0]
        # delete the instance.
        file2.delete()

        # revert the old version
        file_version = Version.objects.get_for_object(file1)[0]
        file_version.revert()

        # reload the reverted instance and check for its content
        file1 = FileModel.objects.all()[0]
        self.assertEqual(file1.test_file.file.read(), 'content1')
