# -*- coding: utf-8 -*-
import json
import shutil
from os.path import join

from cms.api import add_plugin, create_page
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse
from django.utils.http import urlencode

from djangocms_text_ckeditor.models import Text
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.encoding import force_text

from cms.models import Page, Title, Placeholder, StaticPlaceholder
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils.project.fileapp.models import FileModel
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import (
    CMSTestCase, TransactionCMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_ADD,
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_DELETE
)
from cms.utils.reversion_hacks import Revision, reversion, Version


class BasicReversionTestCase(CMSTestCase):
    def setUp(self):
        self.user = self._create_user("test", True, True)

    def test_number_revisions(self):
        with self.login_user_context(self.user):
            self.assertEqual(Revision.objects.all().count(), 0)
            self.page_data = self.get_new_page_data()

            response = self.client.post(URL_CMS_PAGE_ADD, self.page_data)

            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(Revision.objects.all().count(), 1)


class ReversionTestCase(TransactionCMSTestCase):

    def setUp(self):
        u = self._create_user("test", True, True)

        with self.login_user_context(u):
            # add a new text plugin
            self.page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, self.page_data)
            self.assertRedirects(response, URL_CMS_PAGE)

            page = Page.objects.all()[0]
            placeholderpk = page.placeholders.get(slot="body").pk
            post_data = {}
            get_data = {
                'plugin_type': "TextPlugin",
                'plugin_language': settings.LANGUAGES[0][0],
                'placeholder_id': placeholderpk,
            }
            add_url = URL_CMS_PLUGIN_ADD + '?' + urlencode(get_data)
            response = self.client.post(add_url, post_data)
            self.assertEqual(response.status_code, 302)
            # now edit the plugin
            pk = CMSPlugin.objects.all()[0].pk
            edit_url = URL_CMS_PLUGIN_EDIT + str(pk) + "/"
            response = self.client.get(edit_url)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(edit_url, {"body": "Hello World"})
            self.assertEqual(response.status_code, 200)
            txt = Text.objects.all()[0]
            self.assertEqual("Hello World", txt.body)
            self.txt = txt
            # change the content
            response = self.client.post(edit_url, {"body": "Bye Bye World"})
            self.assertEqual(response.status_code, 200)
            txt = Text.objects.all()[0]
            self.assertEqual("Bye Bye World", txt.body)
            p_data = self.page_data.copy()
            response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, p_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            page.publish('en')

        self.user = u

    def get_example_admin(self):
        admin.autodiscover()
        return admin.site._registry[Example1]

    def get_page_admin(self):
        admin.autodiscover()
        return admin.site._registry[Page]

    def get_staticplaceholder_admin(self):
        admin.autodiscover()
        return admin.site._registry[StaticPlaceholder]

    def get_post_request(self, data):
        return self.get_request(post_data=data)

    def test_revision_on_plugin_move(self):
        from cms.plugin_pool import plugin_pool

        placeholder_c_type = ContentType.objects.get_for_model(Placeholder)
        placeholder_versions = Version.objects.filter(content_type=placeholder_c_type)

        LinkPluginModel = plugin_pool.get_plugin('LinkPlugin').model
        link_plugin_c_type = ContentType.objects.get_for_model(LinkPluginModel)

        # three placeholder types
        # native - native CMS placeholder (created using a placeholder tag)
        # manual - Manual placeholder (created using a PlaceholderField)
        # static - Static placeholder (created using the staticplaceholder tag)

        native_placeholder_page = create_page('test page', 'simple.html', u'en')
        native_placeholder = native_placeholder_page.placeholders.get(slot='placeholder')
        native_placeholder_pk = native_placeholder.pk
        native_placeholder_admin = self.get_page_admin()
        native_placeholder_versions = placeholder_versions.filter(object_id_int=native_placeholder_pk)
        native_placeholder_versions_initial_count = native_placeholder_versions.count()

        example = Example1.objects.create(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four',
        )
        manual_placeholder = example.placeholder
        manual_placeholder_admin = self.get_example_admin()

        static_placeholder_obj = StaticPlaceholder.objects.create(
            name='static',
            code='static',
            site_id=1,
        )
        static_placeholder = static_placeholder_obj.draft
        static_placeholder_admin = self.get_staticplaceholder_admin()

        data = {
            'placeholder': native_placeholder,
            'plugin_type': 'LinkPlugin',
            'language': 'en',
        }

        # Add plugin to feature
        link_plugin = add_plugin(**data)
        link_plugin_pk = link_plugin.pk
        link_plugin_versions = Version.objects.filter(
            content_type=link_plugin_c_type,
            object_id_int=link_plugin_pk,
        )
        link_plugin_versions_initial_count = link_plugin_versions.count()

        # move plugin to manual placeholder
        request = self.get_post_request({
            'placeholder_id': manual_placeholder.pk,
            'plugin_id': link_plugin_pk,
        })
        response = native_placeholder_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            native_placeholder_versions.count(),
            native_placeholder_versions_initial_count + 1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            Revision.objects.latest('pk').comment,
            'Moved plugins to %s' % force_text(manual_placeholder),
        )

        # move plugin back to native
        request = self.get_post_request({
            'placeholder_id': native_placeholder_pk,
            'plugin_id': link_plugin_pk,
        })
        response = manual_placeholder_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            native_placeholder_versions.count(),
            native_placeholder_versions_initial_count + 2,
        )

        # assert a new version for the link plugin has been created
        self.assertEqual(
            link_plugin_versions.count(),
            link_plugin_versions_initial_count + 1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            Revision.objects.latest('pk').comment,
            'Moved plugins to %s' % force_text(native_placeholder),
        )

        # move plugin to static placeholder
        request = self.get_post_request({
            'placeholder_id': static_placeholder.pk,
            'plugin_id': link_plugin_pk,
        })
        response = native_placeholder_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            native_placeholder_versions.count(),
            native_placeholder_versions_initial_count + 3,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            Revision.objects.latest('pk').comment,
            'Moved plugins to %s' % force_text(static_placeholder),
        )

        # move plugin back to native
        request = self.get_post_request({
            'placeholder_id': native_placeholder.pk,
            'plugin_id': link_plugin_pk,
        })
        response = static_placeholder_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            native_placeholder_versions.count(),
            native_placeholder_versions_initial_count + 4,
        )

        # assert a new version for the link plugin has been created
        self.assertEqual(
            link_plugin_versions.count(),
            link_plugin_versions_initial_count + 2,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            Revision.objects.latest('pk').comment,
            'Moved plugins to %s' % force_text(native_placeholder),
        )

    def test_revision_on_plugin_move_a_copy(self):
        from cms.plugin_pool import plugin_pool

        def get_plugin_id_from_response(response):
            # Expects response to be a JSON response
            # with a structure like so:
            # {"urls": {"edit_plugin": "/en/admin/placeholderapp/example1/edit-plugin/3/"}
            data = json.loads(response.content.decode('utf-8'))
            return data['urls']['edit_plugin'].split('/')[-2]

        placeholder_c_type = ContentType.objects.get_for_model(Placeholder)
        placeholder_versions = Version.objects.filter(content_type=placeholder_c_type)
        placeholder_versions_initial_count = placeholder_versions.count()

        LinkPluginModel = plugin_pool.get_plugin('LinkPlugin').model
        link_plugin_c_type = ContentType.objects.get_for_model(LinkPluginModel)

        # three placeholder types
        # native - native CMS placeholder (created using a placeholder tag)
        # manual - Manual placeholder (created using a PlaceholderField)
        # static - Static placeholder (created using the staticplaceholder tag)

        native_placeholder_page = create_page('test page', 'simple.html', u'en')
        native_placeholder = native_placeholder_page.placeholders.get(slot='placeholder')
        native_placeholder_pk = native_placeholder.pk
        native_placeholder_admin = self.get_page_admin()
        native_placeholder_versions = placeholder_versions.filter(object_id_int=native_placeholder_pk)
        native_placeholder_versions_initial_count = native_placeholder_versions.count()

        example = Example1.objects.create(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four',
        )
        manual_placeholder = example.placeholder
        manual_placeholder_admin = self.get_example_admin()

        static_placeholder_obj = StaticPlaceholder.objects.create(
            name='static',
            code='static',
            site_id=1,
        )
        static_placeholder = static_placeholder_obj.draft
        static_placeholder_admin = self.get_staticplaceholder_admin()

        # Add plugin to manual placeholder
        data = {
            'placeholder': manual_placeholder,
            'plugin_type': 'LinkPlugin',
            'language': 'en',
        }

        link_plugin = add_plugin(**data)
        link_plugin_versions = Version.objects.filter(
            content_type=link_plugin_c_type,
        )

        # copy plugin from manual to native placeholder
        request = self.get_post_request({
            'placeholder_id': native_placeholder.pk,
            'plugin_id': link_plugin.pk,
            'plugin_order': ['__COPY__'],
            'move_a_copy': 'true',
        })
        response = manual_placeholder_admin.move_plugin(request)

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        link_plugin_pk = get_plugin_id_from_response(response)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            native_placeholder_versions.count(),
            native_placeholder_versions_initial_count + 1,
        )

        # assert a new version for the link plugin has been created
        self.assertEqual(
            link_plugin_versions.filter(object_id_int=link_plugin_pk).count(),
            1,
        )

        # Assert revision comment was set correctly
        self.assertEqual(
            Revision.objects.latest('pk').comment,
            'Copied plugins to %s' % force_text(native_placeholder),
        )

        # copy plugin from native to manual placeholder
        request = self.get_post_request({
            'placeholder_id': manual_placeholder.pk,
            'plugin_id': link_plugin_pk,
            'plugin_order': ['__COPY__'],
            'move_a_copy': 'true',
        })
        response = native_placeholder_admin.move_plugin(request)

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        link_plugin_pk = get_plugin_id_from_response(response)

        # assert revision count remains the same
        self.assertEqual(
            placeholder_versions.count(),
            placeholder_versions_initial_count + 1,
        )

        # copy plugin from manual to static placeholder
        request = self.get_post_request({
            'placeholder_id': static_placeholder.pk,
            'plugin_id': link_plugin_pk,
            'plugin_order': ['__COPY__'],
            'move_a_copy': 'true',
        })
        response = manual_placeholder_admin.move_plugin(request)

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        link_plugin_pk = get_plugin_id_from_response(response)

        # assert revision count remains the same
        self.assertEqual(
            placeholder_versions.count(),
            placeholder_versions_initial_count + 1,
        )

        # copy plugin from static to manual placeholder
        request = self.get_post_request({
            'placeholder_id': manual_placeholder.pk,
            'plugin_id': link_plugin_pk,
            'plugin_order': ['__COPY__'],
            'move_a_copy': 'true',
        })
        response = static_placeholder_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert revision count remains the same
        self.assertEqual(
            placeholder_versions.count(),
            placeholder_versions_initial_count + 1,
        )

        # copy plugin from static to native placeholder
        request = self.get_post_request({
            'placeholder_id': native_placeholder.pk,
            'plugin_id': link_plugin_pk,
            'plugin_order': ['__COPY__'],
            'move_a_copy': 'true',
        })
        response = static_placeholder_admin.move_plugin(request)

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        link_plugin_pk = get_plugin_id_from_response(response)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            native_placeholder_versions.count(),
            native_placeholder_versions_initial_count + 2,
        )

        # assert a new version for the link plugin has been created
        self.assertEqual(
            link_plugin_versions.filter(object_id_int=link_plugin_pk).count(),
            1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            Revision.objects.latest('pk').comment,
            'Copied plugins to %s' % force_text(native_placeholder),
        )

    def test_revert(self):
        """
        Test that you can revert a plugin
        """
        with self.login_user_context(self.user):
            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(Title.objects.all().count(), 2)
            self.assertEqual(CMSPlugin.objects.all().count(), 2)
            self.assertEqual(Revision.objects.all().count(), 4)

            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.all()[1]
            version = Version.objects.get(content_type=ctype, revision=revision)
            page = Page.objects.all()[0]

            history_url = '%s%s/%s/' % (URL_CMS_PAGE, str(page.pk), "history")
            response = self.client.get(history_url)
            self.assertEqual(response.status_code, 200)

            revert_url = history_url + "%s/" % version.pk
            response = self.client.post("%s?language=en&" % revert_url)
            self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page.pk)
            # test for publisher_is_draft, published is set for both draft and
            # published page
            self.assertEqual(Page.objects.all()[0].publisher_is_draft, True)
            self.assertEqual(CMSPlugin.objects.all().count(), 2)

            # test that CMSPlugin subclasses are reverted
            self.assertEqual(Text.objects.all().count(), 2)
            self.assertEqual(Text.objects.get(pk=self.txt.pk).body, "Hello World")
            self.assertEqual(Revision.objects.all().count(), 5)

    def test_undo_redo(self):
        """
        Test that you can revert a plugin
        """
        with self.login_user_context(self.user):
            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(Title.objects.all().count(), 2)
            self.assertEqual(CMSPlugin.objects.all().count(), 2)
            self.assertEqual(Revision.objects.all().count(), 4)
            self.assertEqual(Placeholder.objects.count(), 5)

            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.all()[2]
            Version.objects.get(content_type=ctype, revision=revision)
            page = Page.objects.all()[0]

            undo_url = admin_reverse("cms_page_undo", args=[page.pk])
            response = self.client.post(undo_url)
            self.assertEqual(response.status_code, 200)
            page = Page.objects.all()[0]
            self.assertTrue(page.revision_id != 0)
            rev = page.revision_id
            redo_url = admin_reverse("cms_page_redo", args=[page.pk])
            response = self.client.post(redo_url)
            self.assertEqual(response.status_code, 200)
            page = Page.objects.all()[0]
            self.assertTrue(page.revision_id != rev)
            txt = Text.objects.all()[0]
            edit_url = URL_CMS_PLUGIN_EDIT + str(txt.pk) + "/"
            response = self.client.post(edit_url, {"body": "Hello World2"})
            self.assertEqual(response.status_code, 200)
            page = Page.objects.all()[0]
            self.assertEqual(page.revision_id, 0)
            self.assertEqual(2, CMSPlugin.objects.all().count())
            placeholderpk = page.placeholders.filter(slot="body")[0].pk
            post_data = {}
            get_data = {
                'plugin_type': "TextPlugin",
                'plugin_language': settings.LANGUAGES[0][0],
                'placeholder_id': placeholderpk,
            }
            add_url = URL_CMS_PLUGIN_ADD + '?' + urlencode(get_data)
            response = self.client.post(add_url, post_data)
            self.assertEqual(response.status_code, 302)
            pk = CMSPlugin.objects.all()[2].pk
            # now edit the plugin
            edit_url = URL_CMS_PLUGIN_EDIT + str(pk) + "/"
            response = self.client.get(edit_url)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(edit_url, {"body": "Hello World"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(3, CMSPlugin.objects.all().count())
            self.client.post(undo_url)
            self.client.post(undo_url)
            self.assertEqual(2, CMSPlugin.objects.all().count())
            self.assertEqual(Placeholder.objects.count(), 5)

    def test_undo_slug_collision(self):
        data1 = self.get_new_page_data()
        data2 = self.get_new_page_data()
        data1['slug'] = 'page1'
        data2['slug'] = 'page2'
        with self.login_user_context(self.get_superuser()):
            response = self.client.post(URL_CMS_PAGE_ADD, data1)
            self.assertEqual(response.status_code, 302)
            response = self.client.post(URL_CMS_PAGE_ADD, data2)
            self.assertEqual(response.status_code, 302)
            page1 = Page.objects.get(title_set__slug='page1')
            page2 = Page.objects.get(title_set__slug='page2')
            data1['slug'] = 'page3'
            response = self.client.post(URL_CMS_PAGE_CHANGE % page1.pk, data1)
            self.assertEqual(response.status_code, 302)
            data2['slug'] = 'page1'
            response = self.client.post(URL_CMS_PAGE_CHANGE % page2.pk, data2)
            self.assertEqual(response.status_code, 302)

            undo_url = admin_reverse("cms_page_undo", args=[page1.pk])
            response = self.client.post(undo_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Title.objects.get(page=page1).slug, 'page3')
            response = self.client.get(admin_reverse("cms_page_changelist"))
            self.assertEqual(response.status_code, 200)
            response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            self.assertEqual(response.status_code, 200)
            response = self.client.get('/en/page1/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            self.assertEqual(response.status_code, 200)

    def test_recover(self):
        """
        Test that you can recover a page
        """
        with self.login_user_context(self.user):
            self.assertEqual(Revision.objects.all().count(), 4)
            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.all()[3]
            version = Version.objects.filter(content_type=ctype, revision=revision)[0]

            self.assertEqual(Page.objects.all().count(), 2)
            self.assertEqual(CMSPlugin.objects.all().count(), 2)
            self.assertEqual(Text.objects.all().count(), 2)

            page = Page.objects.all()[0]
            page_pk = page.pk
            page.delete()

            self.assertEqual(Page.objects.all().count(), 0)
            self.assertEqual(CMSPlugin.objects.all().count(), 0)
            self.assertEqual(Text.objects.all().count(), 0)

            recover_url = URL_CMS_PAGE + "recover/"
            response = self.client.get(recover_url)
            self.assertEqual(response.status_code, 200)
            recover_url += "%s/" % version.pk
            response = self.client.get(recover_url)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(recover_url, self.page_data)
            self.assertEqual(Page.objects.all().count(), 1)
            self.assertEqual(CMSPlugin.objects.all().count(), 1)

            # test that CMSPlugin subclasses are recovered
            self.assertEqual(Text.objects.all().count(), 1)
            self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page_pk)

    def test_recover_with_apphook(self):
        """
        Test that you can recover a page
        """
        from cms.utils.helpers import make_revision_with_plugins
        from cms.utils.reversion_hacks import create_revision, revision_manager

        self.assertEqual(Page.objects.count(), 2)

        with self.login_user_context(self.user):

            page_data = self.get_new_page_data_dbfields()
            page_data['apphook'] = 'SampleApp'
            page_data['apphook_namespace'] = 'SampleApp'

            with create_revision():
                # Need to create page manually to add apphooks
                page = create_page(**page_data)

                # Assert page has apphooks
                self.assertEqual(page.application_urls, 'SampleApp')
                self.assertEqual(page.application_namespace, 'SampleApp')

                # Create revision
                make_revision_with_plugins(page, user=None, message="Initial version")

            page_pk = page.pk

            # Delete the page through the admin
            data = {'post': 'yes'}
            response = self.client.post(URL_CMS_PAGE_DELETE % page.pk, data)
            self.assertRedirects(response, URL_CMS_PAGE)

            # Assert page was truly deleted
            self.assertEqual(Page.objects.filter(pk=page_pk).count(), 0)

            versions_qs = revision_manager.get_deleted(Page).order_by("-pk")
            version = versions_qs[0]

            recover_url = URL_CMS_PAGE + "recover/%s/" % version.pk

            # Recover deleted page
            page_form_data = self.get_pagedata_from_dbfields(page_data)
            self.client.post(recover_url, page_form_data)

            # Verify page was recovered correctly
            self.assertEqual(Page.objects.filter(pk=page_pk).count(), 1)

            # Get recovered page
            page = Page.objects.get(pk=page_pk)

            # Verify apphook and apphook namespace are set on page.
            self.assertEqual(page.application_urls, 'SampleApp')
            self.assertEqual(page.application_namespace, 'SampleApp')

    def test_recover_path_collision(self):
        with self.login_user_context(self.user):
            self.assertEqual(Page.objects.count(), 2)
            page_data2 = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data2)
            self.assertRedirects(response, URL_CMS_PAGE)

            page_data3 = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data3)
            self.assertRedirects(response, URL_CMS_PAGE)
            page2 = Page.objects.all()[2]
            page3 = Page.objects.all()[3]

            self.assertEqual(page3.path, '0004')

            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.order_by('-pk')[1]
            version = Version.objects.filter(content_type=ctype, revision=revision)[0]
            page2_pk = page2.pk
            page2.delete()
            self.assertEqual(Page.objects.count(), 3)
            page_data4 = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data4)
            self.assertRedirects(response, URL_CMS_PAGE)
            page4 = Page.objects.all()[3]
            self.assertEqual(Page.objects.count(), 4)
            self.assertEqual(page4.path, '0005')

            recover_url = URL_CMS_PAGE + "recover/"
            response = self.client.get(recover_url)
            self.assertEqual(response.status_code, 200)

            recover_url += "%s/" % version.pk
            response = self.client.get(recover_url)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(recover_url, page_data2)
            self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page2_pk)
            self.assertEqual(Page.objects.all().count(), 5)

    def test_publish_limits(self):
        with self.login_user_context(self.user):
            with self.settings(CMS_MAX_PAGE_PUBLISH_REVERSIONS=2, CMS_MAX_PAGE_HISTORY_REVERSIONS=2):
                page = Page.objects.all()[0]
                page_pk = page.pk
                self.assertEqual(Revision.objects.all().count(), 4)
                for x in range(10):
                    publish_url = URL_CMS_PAGE + "%s/en/publish/" % page_pk
                    response = self.client.post(publish_url)
                    self.assertEqual(response.status_code, 302)
                self.assertEqual(Revision.objects.all().count(), 4)


class ReversionFileFieldTests(CMSTestCase):
    def tearDown(self):
        shutil.rmtree(join(settings.MEDIA_ROOT, 'fileapp'))

    def test_file_persistence(self):
        content = b'content1'
        with reversion.create_revision():
            # add a file instance
            file1 = FileModel()
            file1.test_file.save('file1.txt', SimpleUploadedFile('file1.txt', content), False)
            file1.save()
            # manually add a revision because we use the explicit way
            # django-cms uses too.
            adapter = reversion.get_adapter(FileModel)
            reversion.revision_context_manager.add_to_context(
                reversion.default_revision_manager, file1,
                adapter.get_version_data(file1))
        # reload the instance from db
        file2 = FileModel.objects.all()[0]
        # delete the instance.
        file2.delete()

        # revert the old version
        file_version = reversion.get_for_object(file1)[0]
        file_version.revert()

        # reload the reverted instance and check for its content
        file1 = FileModel.objects.all()[0]
        self.assertEqual(file1.test_file.file.read(), content)
