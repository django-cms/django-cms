# -*- coding: utf-8 -*-
from __future__ import with_statement
import base64
import datetime
import json
import os
from distutils.version import LooseVersion
try:
    from django.utils import unittest
except ImportError:
    import unittest

import django
from django import http
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.core import urlresolvers
from django.core.cache import cache
from django.core.exceptions import (
    ValidationError, ImproperlyConfigured, ObjectDoesNotExist)
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.forms.widgets import Media
from django.test.testcases import TestCase
from django.utils import timezone

from cms import api
from cms.constants import PLUGIN_MOVE_ACTION, PLUGIN_COPY_ACTION
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered, DontUsePageAttributeWarning
from cms.models import Page, Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.sitemaps.cms_sitemap import CMSSitemap
from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import (
    Article, Section, ArticlePluginModel,
    FKModel,
    M2MTargetModel)
from cms.test_utils.project.pluginapp.plugins.meta.cms_plugins import (
    TestPlugin, TestPlugin2, TestPlugin3, TestPlugin4, TestPlugin5)
from cms.test_utils.project.pluginapp.plugins.validation.cms_plugins import (
    NonExisitngRenderTemplate, NoRender, NoRenderButChildren, DynTemplate)
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE, URL_CMS_PLUGIN_MOVE, URL_CMS_PAGE_ADD,
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE,
    URL_CMS_PLUGIN_REMOVE, URL_CMS_PAGE_PUBLISH, URL_CMS_PLUGIN_DELETE, URL_CMS_PLUGINS_COPY)
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.conf import get_cms_setting
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.i18n import force_language
from cms.utils.plugins import get_plugins_for_page, get_plugins

from djangocms_googlemap.models import GoogleMap
from djangocms_inherit.cms_plugins import InheritPagePlaceholderPlugin
from djangocms_file.models import File
from djangocms_inherit.models import InheritPagePlaceholder
from djangocms_link.forms import LinkForm
from djangocms_link.models import Link
from djangocms_picture.models import Picture
from djangocms_text_ckeditor.models import Text
from djangocms_text_ckeditor.utils import plugin_tags_to_id_list, plugin_to_tag


class DumbFixturePlugin(CMSPluginBase):
    model = CMSPlugin
    name = "Dumb Test Plugin. It does nothing."
    render_template = ""
    admin_preview = False
    render_plugin = False

    def render(self, context, instance, placeholder):
        return context


class DumbFixturePluginWithUrls(DumbFixturePlugin):
    name = DumbFixturePlugin.name + " With custom URLs."
    render_plugin = False

    def _test_view(self, request):
        return http.HttpResponse("It works")

    def get_plugin_urls(self):
        return [
            url(r'^testview/$', admin.site.admin_view(self._test_view), name='dumbfixtureplugin'),
        ]
plugin_pool.register_plugin(DumbFixturePluginWithUrls)


class PluginsTestBaseCase(CMSTestCase):
    def setUp(self):
        self.super_user = self._create_user("test", True, True)
        self.slave = self._create_user("slave", True)

        self.FIRST_LANG = settings.LANGUAGES[0][0]
        self.SECOND_LANG = settings.LANGUAGES[1][0]

        self._login_context = self.login_user_context(self.super_user)
        self._login_context.__enter__()

    def tearDown(self):
        self._login_context.__exit__(None, None, None)

    def approve_page(self, page):
        response = self.client.get(URL_CMS_PAGE + "%d/approve/" % page.pk)
        self.assertRedirects(response, URL_CMS_PAGE)
        # reload page
        return self.reload_page(page)

    def get_request(self, *args, **kwargs):
        request = super(PluginsTestBaseCase, self).get_request(*args, **kwargs)
        request.placeholder_media = Media()
        request.toolbar = CMSToolbar(request)
        return request

    def get_response_pk(self, response):
        return int(response.content.decode('utf8').split("/edit-plugin/")[1].split("/")[0])


class PluginsTestCase(PluginsTestBaseCase):
    def _create_text_plugin_on_page(self, page):
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        self.assertEqual(response.status_code, 200)
        created_plugin_id = self.get_response_pk(response)
        self.assertEqual(created_plugin_id, CMSPlugin.objects.all()[0].pk)
        return created_plugin_id

    def _edit_text_plugin(self, plugin_id, text):
        edit_url = "%s%s/" % (URL_CMS_PLUGIN_EDIT, plugin_id)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        data = {
            "body": text
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        txt = Text.objects.get(pk=plugin_id)
        return txt

    def test_add_edit_plugin(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        created_plugin_id = self._create_text_plugin_on_page(page)
        # now edit the plugin
        txt = self._edit_text_plugin(created_plugin_id, "Hello World")
        self.assertEqual("Hello World", txt.body)
        # edit body, but click cancel button
        data = {
            "body": "Hello World!!",
            "_cancel": True,
        }
        edit_url = '%s%d/' % (URL_CMS_PLUGIN_EDIT, created_plugin_id)
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEqual("Hello World", txt.body)

    def test_plugin_edit_marks_page_dirty(self):
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertEqual(response.status_code, 302)
        page = Page.objects.all()[0]
        response = self.client.post(URL_CMS_PAGE_PUBLISH % (page.pk, 'en'))
        self.assertEqual(response.status_code, 302)
        created_plugin_id = self._create_text_plugin_on_page(page)
        page = Page.objects.all()[0]
        self.assertEqual(page.is_dirty('en'), True)
        response = self.client.post(URL_CMS_PAGE_PUBLISH % (page.pk, 'en'))
        self.assertEqual(response.status_code, 302)
        page = Page.objects.all()[0]
        self.assertEqual(page.is_dirty('en'), False)
        self._edit_text_plugin(created_plugin_id, "Hello World")
        page = Page.objects.all()[0]
        self.assertEqual(page.is_dirty('en'), True)

    def test_plugin_order(self):
        """
        Test that plugin position is saved after creation
        """
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")

        # We check created objects and objects from the DB to be sure the position value
        # has been saved correctly
        text_plugin_1 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        text_plugin_2 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm the second")
        db_plugin_1 = CMSPlugin.objects.get(pk=text_plugin_1.pk)
        db_plugin_2 = CMSPlugin.objects.get(pk=text_plugin_2.pk)

        with self.settings(CMS_PERMISSION=False):
            self.assertEqual(text_plugin_1.position, 0)
            self.assertEqual(db_plugin_1.position, 0)
            self.assertEqual(text_plugin_2.position, 1)
            self.assertEqual(db_plugin_2.position, 1)
            ## Finally we render the placeholder to test the actual content
            rendered_placeholder = ph_en.render(self.get_context(page_en.get_absolute_url(), page=page_en), None)
            self.assertEqual(rendered_placeholder, "I'm the firstI'm the second")

    def test_plugin_order_alt(self):
        """
        Test that plugin position is saved after creation
        """
        draft_page = api.create_page("PluginOrderPage", "col_two.html", "en",
                                     slug="page1", published=False, in_navigation=True)
        placeholder = draft_page.placeholders.get(slot="col_left")

        # We check created objects and objects from the DB to be sure the position value
        # has been saved correctly
        text_plugin_2 = api.add_plugin(placeholder, "TextPlugin", "en", body="I'm the second")
        text_plugin_3 = api.add_plugin(placeholder, "TextPlugin", "en", body="I'm the third")
        # Publish to create a 'live' version
        draft_page.publish('en')
        draft_page = draft_page.reload()
        placeholder = draft_page.placeholders.get(slot="col_left")

        # Add a plugin and move it to the first position
        text_plugin_1 = api.add_plugin(placeholder, "TextPlugin", "en", body="I'm the first")
        data = {
            'placeholder_id': placeholder.id,
            'plugin_id': text_plugin_1.id,
            'plugin_parent': '',
            'plugin_language': 'en',
            'plugin_order[]': [text_plugin_1.id, text_plugin_2.id, text_plugin_3.id],
        }
        self.client.post(URL_CMS_PLUGIN_MOVE, data)

        draft_page.publish('en')
        draft_page = draft_page.reload()
        live_page = draft_page.get_public_object()
        placeholder = draft_page.placeholders.get(slot="col_left")
        live_placeholder = live_page.placeholders.get(slot="col_left")

        with self.settings(CMS_PERMISSION=False):
            self.assertEqual(CMSPlugin.objects.get(pk=text_plugin_1.pk).position, 0)
            self.assertEqual(CMSPlugin.objects.get(pk=text_plugin_2.pk).position, 1)
            self.assertEqual(CMSPlugin.objects.get(pk=text_plugin_3.pk).position, 2)

            ## Finally we render the placeholder to test the actual content
            rendered_placeholder = placeholder.render(self.get_context(draft_page.get_absolute_url(), page=draft_page), None)
            self.assertEqual(rendered_placeholder, "I'm the firstI'm the secondI'm the third")
            rendered_live_placeholder = live_placeholder.render(self.get_context(live_page.get_absolute_url(), page=live_page), None)
            self.assertEqual(rendered_live_placeholder, "I'm the firstI'm the secondI'm the third")

    def test_plugin_breadcrumbs(self):
        """
        Test the plugin breadcrumbs order
        """
        draft_page = api.create_page("home", "col_two.html", "en",
                                     slug="page1", published=False, in_navigation=True)
        placeholder = draft_page.placeholders.get(slot="col_left")

        columns = api.add_plugin(placeholder, "MultiColumnPlugin", "en")
        column = api.add_plugin(placeholder, "ColumnPlugin", "en", target=columns, width='10%')
        text_plugin = api.add_plugin(placeholder, "TextPlugin", "en", target=column, body="I'm the second")
        text_breadcrumbs = text_plugin.get_breadcrumb()
        self.assertEqual(len(columns.get_breadcrumb()), 1)
        self.assertEqual(len(column.get_breadcrumb()), 2)
        self.assertEqual(len(text_breadcrumbs), 3)
        self.assertTrue(text_breadcrumbs[0]['title'], columns.get_plugin_class().name)
        self.assertTrue(text_breadcrumbs[1]['title'], column.get_plugin_class().name)
        self.assertTrue(text_breadcrumbs[2]['title'], text_plugin.get_plugin_class().name)
        self.assertTrue('/edit-plugin/%s/'% columns.pk in text_breadcrumbs[0]['url'])
        self.assertTrue('/edit-plugin/%s/'% column.pk, text_breadcrumbs[1]['url'])
        self.assertTrue('/edit-plugin/%s/'% text_plugin.pk, text_breadcrumbs[2]['url'])

    def test_add_cancel_plugin(self):
        """
        Test that you can cancel a new plugin before editing and
        that the plugin is removed.
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        pk = CMSPlugin.objects.all()[0].pk
        expected = {
            "url": URL_CMS_PLUGIN_EDIT + "%s/" % pk,
            "breadcrumb": [
                {
                    "url": URL_CMS_PLUGIN_EDIT + "%s/" % pk,
                    "title": "Text"
                }
            ],
            'delete': URL_CMS_PLUGIN_DELETE % pk
        }
        output = json.loads(response.content.decode('utf8'))
        self.assertEqual(output, expected)
        # now click cancel instead of editing
        response = self.client.get(output['url'])
        self.assertEqual(response.status_code, 200)
        data = {
            "body": "Hello World",
            "_cancel": True,
        }
        response = self.client.post(output['url'], data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, Text.objects.count())

    def test_extract_images_from_text(self):
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + "%s/" % CMSPlugin.objects.all()[0].pk
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        img_path = os.path.join(os.path.dirname(__file__), 'data', 'image.jpg')
        with open(img_path, 'rb') as fobj:
            img_data = base64.b64encode(fobj.read()).decode('utf-8')
        body = """<p>
            <img alt='' src='data:image/jpeg;base64,{data}' />
        </p>""".format(data=img_data)
        data = {
            "body": body
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)

        txt = Text.objects.all()[0]
        self.assertTrue('id="plugin_obj_%s"' % (txt.pk + 1) in txt.body)

    def test_add_text_plugin_empty_tag(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + "%s/" % CMSPlugin.objects.all()[0].pk
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        data = {
            "body": '<div class="someclass"></div><p>foo</p>'
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEqual('<div class="someclass"></div><p>foo</p>', txt.body)

    def test_add_text_plugin_html_sanitizer(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + "%s/" % CMSPlugin.objects.all()[0].pk
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        data = {
            "body": '<script>var bar="hacked"</script>'
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEqual('&lt;script&gt;var bar="hacked"&lt;/script&gt;', txt.body)

    def test_copy_plugins_method(self):
        """
        Test that CMSPlugin copy does not have side effects
        """
        # create some objects
        page_en = api.create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        page_de = api.create_page("CopyPluginTestPage (DE)", "nav_playground.html", "de")
        ph_en = page_en.placeholders.get(slot="body")
        ph_de = page_de.placeholders.get(slot="body")

        # add the text plugin
        text_plugin_en = api.add_plugin(ph_en, "TextPlugin", "en", body="Hello World")
        self.assertEqual(text_plugin_en.pk, CMSPlugin.objects.all()[0].pk)

        # add a *nested* link plugin
        link_plugin_en = api.add_plugin(ph_en, "LinkPlugin", "en", target=text_plugin_en,
                                        name="A Link", url="https://www.django-cms.org")
        #
        text_plugin_en.body += plugin_to_tag(link_plugin_en)
        text_plugin_en.save()

        # the call above to add a child makes a plugin reload required here.
        text_plugin_en = self.reload(text_plugin_en)

        # setup the plugins to copy
        plugins = [text_plugin_en, link_plugin_en]
        # save the old ids for check
        old_ids = [plugin.pk for plugin in plugins]
        new_plugins = []
        plugins_ziplist = []
        old_parent_cache = {}

        # This is a stripped down version of cms.copy_plugins.copy_plugins_to
        # to low-level testing the copy process
        for plugin in plugins:
            new_plugins.append(plugin.copy_plugin(ph_de, 'de', old_parent_cache))
            plugins_ziplist.append((new_plugins[-1], plugin))

        for idx, plugin in enumerate(plugins):
            inst, _ = new_plugins[idx].get_plugin_instance()
            new_plugins[idx] = inst
            new_plugins[idx].post_copy(plugin, plugins_ziplist)

        for idx, plugin in enumerate(plugins):
            # original plugin instance reference should stay unmodified
            self.assertEqual(old_ids[idx], plugin.pk)
            # new plugin instance should be different from the original
            self.assertNotEqual(new_plugins[idx], plugin.pk)

            # text plugins (both old and new) should contain a reference
            # to the link plugins
            if plugin.plugin_type == 'TextPlugin':
                self.assertTrue('link.png' in plugin.body)
                self.assertTrue('plugin_obj_%s' % plugin.get_children()[0].pk in plugin.body)
                self.assertTrue('link.png' in new_plugins[idx].body)
                self.assertTrue('plugin_obj_%s' % new_plugins[idx].get_children()[0].pk in new_plugins[idx].body)

    def test_plugin_position(self):
        page_en = api.create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        placeholder = page_en.placeholders.get(slot="body")  # ID 2
        placeholder_right = page_en.placeholders.get(slot="right-column")
        columns = api.add_plugin(placeholder, "MultiColumnPlugin", "en")  # ID 1
        column_1 = api.add_plugin(placeholder, "ColumnPlugin", "en", target=columns, width='10%')  # ID 2
        column_2 = api.add_plugin(placeholder, "ColumnPlugin", "en", target=columns, width='30%')  # ID 3
        first_text_plugin = api.add_plugin(placeholder, "TextPlugin", "en", target=column_1, body="I'm the first")  # ID 4
        text_plugin = api.add_plugin(placeholder, "TextPlugin", "en", target=column_1, body="I'm the second")  # ID 5

        returned_1 = copy_plugins_to([text_plugin], placeholder, 'en', column_1.pk)  # ID 6
        returned_2 = copy_plugins_to([text_plugin], placeholder_right, 'en')  # ID 7
        returned_3 = copy_plugins_to([text_plugin], placeholder, 'en', column_2.pk)  # ID 8

        # STATE AT THIS POINT:
        # placeholder
        #     - columns
        #         - column_1
        #             - text_plugin "I'm the first"  created here
        #             - text_plugin "I'm the second" created here
        #             - text_plugin "I'm the second" (returned_1) copied here
        #         - column_2
        #             - text_plugin "I'm the second" (returned_3) copied here
        # placeholder_right
        #     - text_plugin "I'm the second" (returned_2) copied here

        # First plugin in the plugin branch
        self.assertEqual(first_text_plugin.position, 0)
        # Second plugin in the plugin branch
        self.assertEqual(text_plugin.position, 1)
        # Added as third plugin in the same branch as the above
        self.assertEqual(returned_1[0][0].position, 2)
        # First plugin in a placeholder
        self.assertEqual(returned_2[0][0].position, 0)
        # First plugin nested in a plugin
        self.assertEqual(returned_3[0][0].position, 0)

    def test_copy_plugins(self):
        """
        Test that copying plugins works as expected.
        """
        # create some objects
        page_en = api.create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        page_de = api.create_page("CopyPluginTestPage (DE)", "nav_playground.html", "de")
        ph_en = page_en.placeholders.get(slot="body")
        ph_de = page_de.placeholders.get(slot="body")

        # add the text plugin
        text_plugin_en = api.add_plugin(ph_en, "TextPlugin", "en", body="Hello World")
        self.assertEqual(text_plugin_en.pk, CMSPlugin.objects.all()[0].pk)

        # add a *nested* link plugin
        link_plugin_en = api.add_plugin(ph_en, "LinkPlugin", "en", target=text_plugin_en,
                                        name="A Link", url="https://www.django-cms.org")

        # the call above to add a child makes a plugin reload required here.
        text_plugin_en = self.reload(text_plugin_en)

        # check the relations
        self.assertEqual(text_plugin_en.get_children().count(), 1)
        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)

        # just sanity check that so far everything went well
        self.assertEqual(CMSPlugin.objects.count(), 2)

        # copy the plugins to the german placeholder
        copy_plugins_to(ph_en.get_plugins(), ph_de, 'de')

        self.assertEqual(ph_de.cmsplugin_set.filter(parent=None).count(), 1)
        text_plugin_de = ph_de.cmsplugin_set.get(parent=None).get_plugin_instance()[0]
        self.assertEqual(text_plugin_de.get_children().count(), 1)
        link_plugin_de = text_plugin_de.get_children().get().get_plugin_instance()[0]

        # check we have twice as many plugins as before
        self.assertEqual(CMSPlugin.objects.count(), 4)

        # check language plugins
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), 2)
        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), 2)

        text_plugin_en = self.reload(text_plugin_en)
        link_plugin_en = self.reload(link_plugin_en)

        # check the relations in english didn't change
        self.assertEqual(text_plugin_en.get_children().count(), 1)
        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)

        self.assertEqual(link_plugin_de.name, link_plugin_en.name)
        self.assertEqual(link_plugin_de.url, link_plugin_en.url)

        self.assertEqual(text_plugin_de.body, text_plugin_en.body)

        # test subplugin copy
        copy_plugins_to([link_plugin_en], ph_de, 'de')

    def test_deep_copy_plugins(self):
        page_en = api.create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        ph_en = page_en.placeholders.get(slot="body")

        # Grid wrapper 1
        mcol1_en = api.add_plugin(ph_en, "MultiColumnPlugin", "en", position="first-child")

        # Grid column 1.1
        col1_en = api.add_plugin(ph_en, "ColumnPlugin", "en", position="first-child", target=mcol1_en)

        # Grid column 1.2
        col2_en = api.add_plugin(ph_en, "ColumnPlugin", "en", position="first-child", target=mcol1_en)

        # add a *nested* link plugin
        link_plugin_en = api.add_plugin(
            ph_en,
            "LinkPlugin",
            "en",
            target=col2_en,
            name="A Link",
            url="https://www.django-cms.org"
        )

        old_plugins = [mcol1_en, col1_en, col2_en, link_plugin_en]

        page_de = api.create_page("CopyPluginTestPage (DE)", "nav_playground.html", "de")
        ph_de = page_de.placeholders.get(slot="body")

        # Grid wrapper 1
        mcol1_de = api.add_plugin(ph_de, "MultiColumnPlugin", "de", position="first-child")

        # Grid column 1.1
        col1_de = api.add_plugin(ph_de, "ColumnPlugin", "de", position="first-child", target=mcol1_de)

        copy_plugins_to(
            old_plugins=[mcol1_en, col1_en, col2_en, link_plugin_en],
            to_placeholder=ph_de,
            to_language='de',
            parent_plugin_id=col1_de.pk,
        )

        col1_de = self.reload(col1_de)

        new_plugins = col1_de.get_descendants().order_by('path')

        self.assertEqual(new_plugins.count(), len(old_plugins))

        for old_plugin, new_plugin in zip(old_plugins, new_plugins):
            self.assertEqual(old_plugin.numchild, new_plugin.numchild)

        with self.assertNumQueries(FuzzyInt(0, 207)):
            page_en.publish('en')

    def test_plugin_validation(self):
        self.assertRaises(ImproperlyConfigured, plugin_pool.validate_templates, NonExisitngRenderTemplate)
        self.assertRaises(ImproperlyConfigured, plugin_pool.validate_templates, NoRender)
        self.assertRaises(ImproperlyConfigured, plugin_pool.validate_templates, NoRenderButChildren)
        plugin_pool.validate_templates(DynTemplate)

    def test_remove_plugin_before_published(self):
        """
        When removing a draft plugin we would expect the public copy of the plugin to also be removed
        """
        # add a page
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_response_pk(response), CMSPlugin.objects.all()[0].pk)
        # there should be only 1 plugin
        self.assertEqual(CMSPlugin.objects.all().count(), 1)

        # delete the plugin
        plugin_data = {
            'plugin_id': self.get_response_pk(response)
        }
        remove_url = URL_CMS_PLUGIN_REMOVE + "%s/" % self.get_response_pk(response)
        response = self.client.post(remove_url, plugin_data)
        self.assertEqual(response.status_code, 302)
        # there should be no plugins
        self.assertEqual(0, CMSPlugin.objects.all().count())

    def test_remove_plugin_after_published(self):
        # add a page
        api.create_page("home", "nav_playground.html", "en")
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        plugin_id = self.get_response_pk(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_response_pk(response), CMSPlugin.objects.all()[0].pk)

        # there should be only 1 plugin
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        self.assertEqual(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=True).count(), 1)

        # publish page
        response = self.client.post(URL_CMS_PAGE + "%d/en/publish/" % page.pk, {1: 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Page.objects.count(), 3)

        # there should now be two plugins - 1 draft, 1 public
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

        # delete the plugin
        plugin_data = {
            'plugin_id': plugin_id
        }
        remove_url = URL_CMS_PLUGIN_REMOVE + "%s/" % plugin_id
        response = self.client.post(remove_url, plugin_data)
        self.assertEqual(response.status_code, 302)

        # there should be no plugins
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        self.assertEqual(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=False).count(), 1)

    def test_remove_plugin_not_associated_to_page(self):
        """
        Test case for PlaceholderField
        """
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_response_pk(response), CMSPlugin.objects.all()[0].pk)

        # there should be only 1 plugin
        self.assertEqual(CMSPlugin.objects.all().count(), 1)

        ph = Placeholder(slot="subplugin")
        ph.save()
        plugin_data = {
            'plugin_type': "TextPlugin",
            'language': settings.LANGUAGES[0][0],
            'placeholder': ph.pk,
            'parent': self.get_response_pk(response)
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        # no longer allowed for security reasons
        self.assertEqual(response.status_code, 404)

    def test_register_plugin_twice_should_raise(self):
        number_of_plugins_before = len(plugin_pool.get_all_plugins())
        # The first time we register the plugin is should work
        plugin_pool.register_plugin(DumbFixturePlugin)
        # Let's add it a second time. We should catch and exception
        raised = False
        try:
            plugin_pool.register_plugin(DumbFixturePlugin)
        except PluginAlreadyRegistered:
            raised = True
        self.assertTrue(raised)
        # Let's also unregister the plugin now, and assert it's not in the
        # pool anymore
        plugin_pool.unregister_plugin(DumbFixturePlugin)
        # Let's make sure we have the same number of plugins as before:
        number_of_plugins_after = len(plugin_pool.get_all_plugins())
        self.assertEqual(number_of_plugins_before, number_of_plugins_after)

    def test_unregister_non_existing_plugin_should_raise(self):
        number_of_plugins_before = len(plugin_pool.get_all_plugins())
        raised = False
        try:
            # There should not be such a plugin registered if the others tests
            # don't leak plugins
            plugin_pool.unregister_plugin(DumbFixturePlugin)
        except PluginNotRegistered:
            raised = True
        self.assertTrue(raised)
        # Let's count, to make sure we didn't remove a plugin accidentally.
        number_of_plugins_after = len(plugin_pool.get_all_plugins())
        self.assertEqual(number_of_plugins_before, number_of_plugins_after)

    def test_inheritplugin_media(self):
        """
        Test case for InheritPagePlaceholder
        """

        inheritfrompage = api.create_page('page to inherit from',
                                          'nav_playground.html',
                                          'en')

        body = inheritfrompage.placeholders.get(slot="body")

        plugin = GoogleMap(
            plugin_type='GoogleMapPlugin',
            placeholder=body,
            position=1,
            language=settings.LANGUAGE_CODE,
            address="Riedtlistrasse 16",
            zipcode="8006",
            city="Zurich",
        )
        plugin.add_root(instance=plugin)
        inheritfrompage.publish('en')

        page = api.create_page('inherit from page',
                               'nav_playground.html',
                               'en',
                               published=True)

        inherited_body = page.placeholders.get(slot="body")

        inherit_plugin = InheritPagePlaceholder(
            plugin_type='InheritPagePlaceholderPlugin',
            placeholder=inherited_body,
            position=1,
            language=settings.LANGUAGE_CODE,
            from_page=inheritfrompage,
            from_language=settings.LANGUAGE_CODE)
        inherit_plugin.add_root(instance=inherit_plugin)
        page.publish('en')

        self.client.logout()
        cache.clear()
        response = self.client.get(page.get_absolute_url())
        self.assertTrue(
            'https://maps-api-ssl.google.com/maps/api/js' in response.content.decode('utf8').replace("&amp;", "&"))

    def test_inherit_plugin_with_empty_plugin(self):
        inheritfrompage = api.create_page('page to inherit from',
                                          'nav_playground.html',
                                          'en', published=True)

        body = inheritfrompage.placeholders.get(slot="body")
        empty_plugin = CMSPlugin(
            plugin_type='TextPlugin', # create an empty plugin
            placeholder=body,
            position=1,
            language='en',
        )
        empty_plugin.add_root(instance=empty_plugin)
        other_page = api.create_page('other page', 'nav_playground.html', 'en', published=True)
        inherited_body = other_page.placeholders.get(slot="body")

        api.add_plugin(inherited_body, InheritPagePlaceholderPlugin, 'en', position='last-child',
                       from_page=inheritfrompage, from_language='en')

        api.add_plugin(inherited_body, "TextPlugin", "en", body="foobar")
        # this should not fail, even if there in an empty plugin
        rendered = inherited_body.render(context=self.get_context(other_page.get_absolute_url(), page=other_page), width=200)
        self.assertIn("foobar", rendered)

    def test_render_textplugin(self):
        # Setup
        page = api.create_page("render test", "nav_playground.html", "en")
        ph = page.placeholders.get(slot="body")
        text_plugin = api.add_plugin(ph, "TextPlugin", "en", body="Hello World")
        link_plugins = []
        for i in range(0, 10):
            link_plugins.append(api.add_plugin(ph, "LinkPlugin", "en",
                                               target=text_plugin,
                                               name="A Link %d" % i,
                                               url="http://django-cms.org"))
            text_plugin.body += '<img src="/static/cms/img/icons/plugins/link.png" alt="Link - %s" id="plugin_obj_%d" title="Link - %s" />' % (
                link_plugins[-1].name,
                link_plugins[-1].pk,
                link_plugins[-1].name,
            )
        text_plugin.save()
        ph = Placeholder.objects.get(pk=ph.pk)
        text_plugin.body = '\n'.join(['<img id="plugin_obj_%d" src=""/>' % l.cmsplugin_ptr_id for l in link_plugins])
        text_plugin.save()
        text_plugin = self.reload(text_plugin)

        with self.assertNumQueries(2):
            rendered = text_plugin.render_plugin(placeholder=ph)
        for i in range(0, 10):
            self.assertTrue('A Link %d' % i in rendered)

    def test_copy_textplugin(self):
        """
        Test that copying of textplugins replaces references to copied plugins
        """
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')

        plugin_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=0,
            language=self.FIRST_LANG)
        plugin_base = plugin_base.add_root(instance=plugin_base)
        plugin = Text(body='')
        plugin_base.set_base_attr(plugin)
        plugin.save()

        plugin_ref_1_base = CMSPlugin(
            plugin_type='EmptyPlugin',
            placeholder=placeholder,
            position=0,
            language=self.FIRST_LANG)
        plugin_ref_1_base = plugin_base.add_child(instance=plugin_ref_1_base)
        plugin_ref_2_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG)
        plugin_ref_2_base = plugin_base.add_child(instance=plugin_ref_2_base)
        plugin_ref_2 = Text(body='')
        plugin_ref_2_base.set_base_attr(plugin_ref_2)

        plugin_ref_2.save()

        plugin.body = ' <img id="plugin_obj_%s" src=""/><img id="plugin_obj_%s" src=""/>' % (
            str(plugin_ref_1_base.pk), str(plugin_ref_2.pk))
        plugin.save()

        page_data = self.get_new_page_data()

        #create 2nd language page
        page_data.update({
            'language': self.SECOND_LANG,
            'title': "%s %s" % (page.get_title(), self.SECOND_LANG),
        })
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % self.SECOND_LANG, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)

        self.assertEqual(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
        self.assertEqual(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
        self.assertEqual(CMSPlugin.objects.count(), 3)
        self.assertEqual(Page.objects.all().count(), 1)

        copy_data = {
            'source_placeholder_id': placeholder.pk,
            'target_placeholder_id': placeholder.pk,
            'target_language': self.SECOND_LANG,
            'source_language': self.FIRST_LANG,
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf8').count('"position":'), 3)
        # assert copy success
        self.assertEqual(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
        self.assertEqual(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 3)
        self.assertEqual(CMSPlugin.objects.count(), 6)
        plugins = list(CMSPlugin.objects.all())
        new_plugin = plugins[3].get_plugin_instance()[0]
        idlist = sorted(plugin_tags_to_id_list(new_plugin.body))
        expected = sorted([plugins[4].pk, plugins[5].pk])
        self.assertEqual(idlist, expected)

    @unittest.skipIf(LooseVersion(django.get_version()) < LooseVersion('1.7'),
                     reason='test not supported in Django 1.6')
    def test_search_pages(self):
        """
        Test search for pages
        To be fully useful, this testcase needs to have the following different
        Plugin configurations within the project:
            * unaltered cmsplugin_ptr
            * cmsplugin_ptr with related_name='+'
            * cmsplugin_ptr with related_query_name='+'
            * cmsplugin_ptr with related_query_name='whatever_foo'
            * cmsplugin_ptr with related_name='whatever_bar'
            * cmsplugin_ptr with related_query_name='whatever_foo' and related_name='whatever_bar'
        Those plugins are in cms/test_utils/project/pluginapp/revdesc/models.py
        """
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')
        text = Text(body="hello", language="en", placeholder=placeholder, plugin_type="TextPlugin", position=1)
        text.save()
        page.publish('en')
        self.assertEqual(Page.objects.search("hi").count(), 0)
        self.assertEqual(Page.objects.search("hello").count(), 1)

    def test_empty_plugin_is_not_ignored(self):
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')

        plugin = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG)
        plugin.add_root(instance=plugin)

        # this should not raise any errors, but just ignore the empty plugin
        out = placeholder.render(self.get_context(), width=300)
        self.assertFalse(len(out))
        self.assertTrue(len(placeholder._plugins_cache))

    def test_defer_pickel(self):
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')
        api.add_plugin(placeholder, "TextPlugin", 'en', body="Hello World")
        plugins = Text.objects.all().defer('path')
        import pickle
        import io
        a = io.BytesIO()
        pickle.dump(plugins[0], a)


    def test_empty_plugin_description(self):
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')
        a = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG
        )

        self.assertEqual(a.get_short_description(), "<Empty>")

    def test_page_attribute_warns(self):
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')
        a = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG
        )
        a.save()

        def get_page(plugin):
            return plugin.page

        self.assertWarns(
            DontUsePageAttributeWarning,
            "Don't use the page attribute on CMSPlugins! CMSPlugins are not guaranteed to have a page associated with them!",
            get_page, a
        )

    def test_set_translatable_content(self):
        a = Text(body="hello")
        self.assertTrue(a.set_translatable_content({'body': 'world'}))
        b = Link(name="hello")
        self.assertTrue(b.set_translatable_content({'name': 'world'}))


    def test_editing_plugin_changes_page_modification_time_in_sitemap(self):
        now = timezone.now()
        one_day_ago = now - datetime.timedelta(days=1)
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        title = page.get_title_obj('en')
        page.creation_date = one_day_ago
        page.changed_date = one_day_ago
        plugin_id = self._create_text_plugin_on_page(page)
        plugin = self._edit_text_plugin(plugin_id, "fnord")

        actual_last_modification_time = CMSSitemap().lastmod(title)
        actual_last_modification_time -= datetime.timedelta(microseconds=actual_last_modification_time.microsecond)
        self.assertEqual(plugin.changed_date.date(), actual_last_modification_time.date())

    def test_moving_plugin_to_different_placeholder(self):
        plugin_pool.register_plugin(DumbFixturePlugin)
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        plugin_data = {
            'plugin_type': 'DumbFixturePlugin',
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot='body').pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)

        plugin_data['plugin_parent'] = self.get_response_pk(response)
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)

        post = {
            'plugin_id': self.get_response_pk(response),
            'placeholder_id': page.placeholders.get(slot='right-column').pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_MOVE, post)
        self.assertEqual(response.status_code, 200)

        from cms.utils.plugins import build_plugin_tree
        build_plugin_tree(page.placeholders.get(slot='right-column').get_plugins_list())
        plugin_pool.unregister_plugin(DumbFixturePlugin)

    def test_get_plugins_for_page(self):
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm inside an existing placeholder.")
        # This placeholder is not in the template.
        ph_en_not_used = page_en.placeholders.create(slot="not_used")
        text_plugin_2 = api.add_plugin(ph_en_not_used, "TextPlugin", "en", body="I'm inside a non-existent placeholder.")
        page_plugins = get_plugins_for_page(None, page_en, page_en.get_title_obj_attribute('language'))
        db_text_plugin_1 = page_plugins.get(pk=text_plugin_1.pk)
        self.assertRaises(CMSPlugin.DoesNotExist, page_plugins.get, pk=text_plugin_2.pk)
        self.assertEqual(db_text_plugin_1.pk, text_plugin_1.pk)

    def test_plugin_move_with_reload(self):
        action_options = {
            PLUGIN_MOVE_ACTION: {
                'requires_reload': True
            },
            PLUGIN_COPY_ACTION: {
                'requires_reload': True
            },
        }
        non_reload_action_options = {
            PLUGIN_MOVE_ACTION: {
                'requires_reload': False
            },
            PLUGIN_COPY_ACTION: {
                'requires_reload': False
            },
        }
        ReloadDrivenPlugin = type('ReloadDrivenPlugin', (CMSPluginBase,), dict(action_options=action_options, render_plugin=False))
        NonReloadDrivenPlugin = type('NonReloadDrivenPlugin', (CMSPluginBase,), dict(action_options=non_reload_action_options, render_plugin=False))
        plugin_pool.register_plugin(ReloadDrivenPlugin)
        plugin_pool.register_plugin(NonReloadDrivenPlugin)
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        source_placeholder = page.placeholders.get(slot='body')
        target_placeholder = page.placeholders.get(slot='right-column')

        plugin_1 = api.add_plugin(source_placeholder, ReloadDrivenPlugin, settings.LANGUAGES[0][0])
        plugin_2 = api.add_plugin(source_placeholder, NonReloadDrivenPlugin, settings.LANGUAGES[0][0])

        with force_language('en'):
            plugin_1_action_urls = plugin_1.get_action_urls()

        reload_expected = {
            'reload': True,
            'urls': plugin_1_action_urls,
        }

        # Test Plugin reload == True on Move
        post = {
            'plugin_id': plugin_1.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_MOVE, post)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode('utf8')), reload_expected)

        with force_language('en'):
            plugin_2_action_urls = plugin_2.get_action_urls()

        no_reload_expected = {
            'reload': False,
            'urls': plugin_2_action_urls,
        }

        # Test Plugin reload == False on Move
        post = {
            'plugin_id': plugin_2.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_MOVE, post)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode('utf8')), no_reload_expected)

        plugin_pool.unregister_plugin(ReloadDrivenPlugin)
        plugin_pool.unregister_plugin(NonReloadDrivenPlugin)

    def test_plugin_copy_with_reload(self):
        action_options = {
            PLUGIN_MOVE_ACTION: {
                'requires_reload': True
            },
            PLUGIN_COPY_ACTION: {
                'requires_reload': True
            },
        }
        non_reload_action_options = {
            PLUGIN_MOVE_ACTION: {
                'requires_reload': False
            },
            PLUGIN_COPY_ACTION: {
                'requires_reload': False
            },
        }
        ReloadDrivenPlugin = type('ReloadDrivenPlugin', (CMSPluginBase,), dict(action_options=action_options, render_plugin=False))
        NonReloadDrivenPlugin = type('NonReloadDrivenPlugin', (CMSPluginBase,), dict(action_options=non_reload_action_options, render_plugin=False))
        plugin_pool.register_plugin(ReloadDrivenPlugin)
        plugin_pool.register_plugin(NonReloadDrivenPlugin)
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        source_placeholder = page.placeholders.get(slot='body')
        target_placeholder = page.placeholders.get(slot='right-column')
        api.add_plugin(source_placeholder, ReloadDrivenPlugin, settings.LANGUAGES[0][0])
        plugin_2 = api.add_plugin(source_placeholder, NonReloadDrivenPlugin, settings.LANGUAGES[0][0])

        # Test Plugin reload == True on Copy
        copy_data = {
            'source_placeholder_id': source_placeholder.pk,
            'target_placeholder_id': target_placeholder.pk,
            'target_language': settings.LANGUAGES[0][0],
            'source_language': settings.LANGUAGES[0][0],
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content.decode('utf8'))
        self.assertEqual(json_response['reload'], True)

        # Test Plugin reload == False on Copy
        copy_data = {
            'source_placeholder_id': source_placeholder.pk,
            'source_plugin_id': plugin_2.pk,
            'target_placeholder_id': target_placeholder.pk,
            'target_language': settings.LANGUAGES[0][0],
            'source_language': settings.LANGUAGES[0][0],
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content.decode('utf8'))
        self.assertEqual(json_response['reload'], False)

        plugin_pool.unregister_plugin(ReloadDrivenPlugin)
        plugin_pool.unregister_plugin(NonReloadDrivenPlugin)

    def test_custom_plugin_urls(self):
        plugin_url = urlresolvers.reverse('admin:dumbfixtureplugin')

        response = self.client.get(plugin_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"It works")

    def test_plugin_require_parent(self):
        """
        Assert that a plugin marked as 'require_parent' is not listed
        in the plugin pool when a placeholder is specified
        """
        ParentRequiredPlugin = type('ParentRequiredPlugin', (CMSPluginBase,),
                                    dict(require_parent=True, render_plugin=False))
        plugin_pool.register_plugin(ParentRequiredPlugin)
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')

        plugin_list = plugin_pool.get_all_plugins(placeholder=placeholder, page=page)
        self.assertFalse(ParentRequiredPlugin in plugin_list)
        plugin_pool.unregister_plugin(ParentRequiredPlugin)

    def test_plugin_parent_classes(self):
        """
        Assert that a plugin with a list of parent classes only appears in the
        toolbar plugin struct for those given parent Plugins
        """
        ParentClassesPlugin = type('ParentClassesPlugin', (CMSPluginBase,),
                                   dict(parent_classes=['GenericParentPlugin'], render_plugin=False))
        GenericParentPlugin = type('GenericParentPlugin', (CMSPluginBase,), {'render_plugin':False})
        KidnapperPlugin = type('KidnapperPlugin', (CMSPluginBase,), {'render_plugin':False})

        expected_struct = {'module': u'Generic',
                           'name': u'Parent Classes Plugin',
                           'value': 'ParentClassesPlugin'}

        for plugin in [ParentClassesPlugin, GenericParentPlugin, KidnapperPlugin]:
            plugin_pool.register_plugin(plugin)

        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')

        from cms.utils.placeholder import get_toolbar_plugin_struct
        toolbar_struct = get_toolbar_plugin_struct([ParentClassesPlugin],
                                                   placeholder.slot,
                                                   page,
                                                   parent=GenericParentPlugin)
        self.assertTrue(expected_struct in toolbar_struct)

        toolbar_struct = get_toolbar_plugin_struct([ParentClassesPlugin],
                                                   placeholder.slot,
                                                   page,
                                                   parent=KidnapperPlugin)
        self.assertFalse(expected_struct in toolbar_struct)

        toolbar_struct = get_toolbar_plugin_struct([ParentClassesPlugin, GenericParentPlugin],
                                                   placeholder.slot,
                                                   page)
        expected_struct = {'module': u'Generic',
                           'name': u'Generic Parent Plugin',
                           'value': 'GenericParentPlugin'}
        self.assertTrue(expected_struct in toolbar_struct)
        for plugin in [ParentClassesPlugin, GenericParentPlugin, KidnapperPlugin]:
            plugin_pool.unregister_plugin(plugin)

    def test_plugin_child_classes_from_settings(self):
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ChildClassesPlugin = type('ChildClassesPlugin', (CMSPluginBase,),
                                  dict(child_classes=['TextPlugin'], render_template='allow_children_plugin.html'))
        plugin_pool.register_plugin(ChildClassesPlugin)
        plugin = api.add_plugin(placeholder, ChildClassesPlugin, settings.LANGUAGES[0][0])
        plugin = plugin.get_plugin_class_instance()
        ## assert baseline
        self.assertEqual(['TextPlugin'], plugin.get_child_classes(placeholder.slot, page))

        CMS_PLACEHOLDER_CONF = {
            'body': {
                'child_classes': {
                    'ChildClassesPlugin': ['LinkPlugin', 'PicturePlugin'],
                }
            }
        }
        with self.settings(CMS_PLACEHOLDER_CONF=CMS_PLACEHOLDER_CONF):
            self.assertEqual(['LinkPlugin', 'PicturePlugin'],
                             plugin.get_child_classes(placeholder.slot, page))
        plugin_pool.unregister_plugin(ChildClassesPlugin)

    def test_plugin_parent_classes_from_settings(self):
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ParentClassesPlugin = type('ParentClassesPlugin', (CMSPluginBase,),
                                   dict(parent_classes=['TextPlugin'], render_plugin=False))
        plugin_pool.register_plugin(ParentClassesPlugin)
        plugin = api.add_plugin(placeholder, ParentClassesPlugin, settings.LANGUAGES[0][0])
        plugin = plugin.get_plugin_class_instance()
        ## assert baseline
        self.assertEqual(['TextPlugin'], plugin.get_parent_classes(placeholder.slot, page))

        CMS_PLACEHOLDER_CONF = {
            'body': {
                'parent_classes': {
                    'ParentClassesPlugin': ['TestPlugin'],
                }
            }
        }
        with self.settings(CMS_PLACEHOLDER_CONF=CMS_PLACEHOLDER_CONF):
            self.assertEqual(['TestPlugin'],
                             plugin.get_parent_classes(placeholder.slot, page))
        plugin_pool.unregister_plugin(ParentClassesPlugin)

    def test_plugin_translatable_content_getter_setter(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        created_plugin_id = self._create_text_plugin_on_page(page)

        # now edit the plugin
        plugin = self._edit_text_plugin(created_plugin_id, "Hello World")
        self.assertEqual("Hello World", plugin.body)

        # see if the getter works
        self.assertEqual({'body': "Hello World"}, plugin.get_translatable_content())

        # change the content
        self.assertEqual(True, plugin.set_translatable_content({'body': "It works!"}))

        # check if it changed
        self.assertEqual("It works!", plugin.body)

        # double check through the getter
        self.assertEqual({'body': "It works!"}, plugin.get_translatable_content())

    def test_plugin_pool_register_returns_plugin_class(self):
        @plugin_pool.register_plugin
        class DecoratorTestPlugin(CMSPluginBase):
            render_plugin = False
            name = "Test Plugin"
        self.assertIsNotNone(DecoratorTestPlugin)


class FileSystemPluginTests(PluginsTestBaseCase):
    def setUp(self):
        super(FileSystemPluginTests, self).setUp()
        call_command('collectstatic', interactive=False, verbosity=0, link=True)

    def tearDown(self):
        for directory in [settings.STATIC_ROOT, settings.MEDIA_ROOT]:
            for root, dirs, files in os.walk(directory, topdown=False):
                # We need to walk() the directory tree since rmdir() does not allow
                # to remove non-empty directories...
                for name in files:
                    # Start by killing all files we walked
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    # Now all directories we walked...
                    os.rmdir(os.path.join(root, name))
        super(FileSystemPluginTests, self).tearDown()

    def test_fileplugin_icon_uppercase(self):
        page = api.create_page('testpage', 'nav_playground.html', 'en')
        body = page.placeholders.get(slot="body")
        plugin = File(
            plugin_type='FilePlugin',
            placeholder=body,
            position=1,
            language=settings.LANGUAGE_CODE,
        )
        # This try/except block allows older and newer versions of the
        # djangocms-file plugin to work here.
        try:
            plugin.file.save("UPPERCASE.JPG", SimpleUploadedFile(
                "UPPERCASE.jpg", b"content"), False)
        except ObjectDoesNotExist:  # catches 'RelatedObjectDoesNotExist'
            plugin.source.save("UPPERCASE.JPG", SimpleUploadedFile(
                "UPPERCASE.jpg", b"content"), False)
        plugin.add_root(instance=plugin)
        self.assertNotEquals(plugin.get_icon_url().find('jpg'), -1)


class PluginManyToManyTestCase(PluginsTestBaseCase):
    def setUp(self):
        self.super_user = self._create_user("test", True, True)
        self.slave = self._create_user("slave", True)

        self._login_context = self.login_user_context(self.super_user)
        self._login_context.__enter__()

        # create 3 sections
        self.sections = []
        self.section_pks = []
        for i in range(3):
            section = Section.objects.create(name="section %s" % i)
            self.sections.append(section)
            self.section_pks.append(section.pk)
        self.section_count = len(self.sections)
        # create 10 articles by section
        for section in self.sections:
            for j in range(10):
                Article.objects.create(
                    title="article %s" % j,
                    section=section
                )
        self.FIRST_LANG = settings.LANGUAGES[0][0]
        self.SECOND_LANG = settings.LANGUAGES[1][0]

    def test_dynamic_plugin_template(self):
        page_en = api.create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        ph_en = page_en.placeholders.get(slot="body")
        api.add_plugin(ph_en, "ArticleDynamicTemplatePlugin", "en", title="a title")
        api.add_plugin(ph_en, "ArticleDynamicTemplatePlugin", "en", title="custom template")
        request = self.get_request(path=page_en.get_absolute_url())
        plugins = get_plugins(request, ph_en, page_en.template)
        for plugin in plugins:
            if plugin.title == 'custom template':
                self.assertEqual(plugin.get_plugin_class_instance().get_render_template({}, plugin, ph_en), 'articles_custom.html')
                self.assertTrue('Articles Custom template' in plugin.render_plugin({}, ph_en))
            else:
                self.assertEqual(plugin.get_plugin_class_instance().get_render_template({}, plugin, ph_en), 'articles.html')
                self.assertFalse('Articles Custom template' in plugin.render_plugin({}, ph_en))

    def test_add_plugin_with_m2m(self):
        # add a new text plugin
        self.assertEqual(ArticlePluginModel.objects.count(), 0)
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        page.publish('en')
        placeholder = page.placeholders.get(slot="body")
        plugin_data = {
            'plugin_type': "ArticlePlugin",
            'plugin_language': self.FIRST_LANG,
            'plugin_parent': '',
            'placeholder_id': placeholder.pk,
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        pk = CMSPlugin.objects.all()[0].pk
        expected = {
            "url": URL_CMS_PLUGIN_EDIT + "%s/" % pk,
            "breadcrumb": [
                {
                    "url": URL_CMS_PLUGIN_EDIT + "%s/" % pk,
                    "title": "Articles"
                }
            ],
            'delete': URL_CMS_PLUGIN_DELETE % pk
        }
        self.assertEqual(json.loads(response.content.decode('utf8')), expected)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + str(CMSPlugin.objects.all()[0].pk) + "/"
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticlePluginModel.objects.count(), 1)
        plugin = ArticlePluginModel.objects.all()[0]
        self.assertEqual(self.section_count, plugin.sections.count())
        response = self.client.get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(plugin.sections.through._meta.db_table, 'manytomany_rel_articlepluginmodel_sections')

    def test_add_plugin_with_m2m_and_publisher(self):
        self.assertEqual(ArticlePluginModel.objects.count(), 0)
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertEqual(response.status_code, 302)
        page = Page.objects.all()[0]
        placeholder = page.placeholders.get(slot="body")

        # add a plugin
        plugin_data = {
            'plugin_type': "ArticlePlugin",
            'plugin_language': self.FIRST_LANG,
            'plugin_parent': '',
            'placeholder_id': placeholder.pk,

        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        pk = CMSPlugin.objects.all()[0].pk
        expected = {
            "url": URL_CMS_PLUGIN_EDIT + "%s/" % pk,
            "breadcrumb": [
                {
                    "url": URL_CMS_PLUGIN_EDIT + "%s/" % pk,
                    "title": "Articles"
                }
            ],
            'delete': URL_CMS_PLUGIN_DELETE % pk
        }
        self.assertEqual(json.loads(response.content.decode('utf8')), expected)

        # there should be only 1 plugin
        self.assertEqual(1, CMSPlugin.objects.all().count())

        articles_plugin_pk = CMSPlugin.objects.all()[0].pk
        self.assertEqual(articles_plugin_pk, CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + str(CMSPlugin.objects.all()[0].pk) + "/"

        data = {
            'title': "Articles Plugin 1",
            'sections': self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, ArticlePluginModel.objects.count())
        articles_plugin = ArticlePluginModel.objects.all()[0]
        self.assertEqual(u'Articles Plugin 1', articles_plugin.title)
        self.assertEqual(self.section_count, articles_plugin.sections.count())

        # check publish box
        page = api.publish_page(page, self.super_user, 'en')

        # there should now be two plugins - 1 draft, 1 public
        self.assertEqual(2, CMSPlugin.objects.all().count())
        self.assertEqual(2, ArticlePluginModel.objects.all().count())

        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
        expected = [self.section_count for i in range(len(db_counts))]
        self.assertEqual(expected, db_counts)

    def test_copy_plugin_with_m2m(self):
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')

        plugin = ArticlePluginModel(
            plugin_type='ArticlePlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG)
        plugin.add_root(instance=plugin)

        edit_url = URL_CMS_PLUGIN_EDIT + str(plugin.pk) + "/"

        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticlePluginModel.objects.count(), 1)

        self.assertEqual(ArticlePluginModel.objects.all()[0].sections.count(), self.section_count)

        page_data = self.get_new_page_data()

        #create 2nd language page
        page_data.update({
            'language': self.SECOND_LANG,
            'title': "%s %s" % (page.get_title(), self.SECOND_LANG),
        })
        response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk + "?language=%s" % self.SECOND_LANG, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)

        self.assertEqual(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
        self.assertEqual(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
        self.assertEqual(CMSPlugin.objects.count(), 1)
        self.assertEqual(Page.objects.all().count(), 1)
        copy_data = {
            'source_placeholder_id': placeholder.pk,
            'target_placeholder_id': placeholder.pk,
            'target_language': self.SECOND_LANG,
            'source_language': self.FIRST_LANG,
        }
        response = self.client.post(URL_CMS_PLUGINS_COPY, copy_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf8').count('"position":'), 1)
        # assert copy success
        self.assertEqual(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
        self.assertEqual(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 1)
        self.assertEqual(CMSPlugin.objects.count(), 2)
        db_counts = [plgn.sections.count() for plgn in ArticlePluginModel.objects.all()]
        expected = [self.section_count for _ in range(len(db_counts))]
        self.assertEqual(expected, db_counts)


class PluginCopyRelationsTestCase(PluginsTestBaseCase):
    """Test the suggestions in the docs for copy_relations()"""

    def setUp(self):
        self.super_user = self._create_user("test", True, True)
        self.FIRST_LANG = settings.LANGUAGES[0][0]
        self._login_context = self.login_user_context(self.super_user)
        self._login_context.__enter__()
        page_data1 = self.get_new_page_data_dbfields()
        page_data1['published'] = False
        self.page1 = api.create_page(**page_data1)
        page_data2 = self.get_new_page_data_dbfields()
        page_data2['published'] = False
        self.page2 = api.create_page(**page_data2)
        self.placeholder1 = self.page1.placeholders.get(slot='body')
        self.placeholder2 = self.page2.placeholders.get(slot='body')

    def test_copy_fk_from_model(self):
        plugin = api.add_plugin(
            placeholder=self.placeholder1,
            plugin_type="PluginWithFKFromModel",
            language=self.FIRST_LANG,
        )
        FKModel.objects.create(fk_field=plugin)
        old_public_count = FKModel.objects.filter(
            fk_field__placeholder__page__publisher_is_draft=False
        ).count()
        api.publish_page(
            self.page1,
            self.super_user,
            self.FIRST_LANG
        )
        new_public_count = FKModel.objects.filter(
            fk_field__placeholder__page__publisher_is_draft=False
        ).count()
        self.assertEqual(
            new_public_count,
            old_public_count + 1
        )

    def test_copy_m2m_to_model(self):
        plugin = api.add_plugin(
            placeholder=self.placeholder1,
            plugin_type="PluginWithM2MToModel",
            language=self.FIRST_LANG,
        )
        m2m_target = M2MTargetModel.objects.create()
        plugin.m2m_field.add(m2m_target)
        old_public_count = M2MTargetModel.objects.filter(
            pluginmodelwithm2mtomodel__placeholder__page__publisher_is_draft=False
        ).count()
        api.publish_page(
            self.page1,
            self.super_user,
            self.FIRST_LANG
        )
        new_public_count = M2MTargetModel.objects.filter(
            pluginmodelwithm2mtomodel__placeholder__page__publisher_is_draft=False
        ).count()
        self.assertEqual(
            new_public_count,
            old_public_count + 1
        )


class PluginsMetaOptionsTests(TestCase):
    ''' TestCase set for ensuring that bugs like #992 are caught '''

    # these plugins are inlined because, due to the nature of the #992
    # ticket, we cannot actually import a single file with all the
    # plugin variants in, because that calls __new__, at which point the
    # error with splitted occurs.

    def test_meta_options_as_defaults(self):
        ''' handling when a CMSPlugin meta options are computed defaults '''
        # this plugin relies on the base CMSPlugin and Model classes to
        # decide what the app_label and db_table should be

        plugin = TestPlugin.model
        self.assertEqual(plugin._meta.db_table, 'meta_testpluginmodel')
        self.assertEqual(plugin._meta.app_label, 'meta')

    def test_meta_options_as_declared_defaults(self):
        ''' handling when a CMSPlugin meta options are declared as per defaults '''
        # here, we declare the db_table and app_label explicitly, but to the same
        # values as would be computed, thus making sure it's not a problem to
        # supply options.

        plugin = TestPlugin2.model
        self.assertEqual(plugin._meta.db_table, 'meta_testpluginmodel2')
        self.assertEqual(plugin._meta.app_label, 'meta')

    def test_meta_options_custom_app_label(self):
        ''' make sure customised meta options on CMSPlugins don't break things '''

        plugin = TestPlugin3.model
        self.assertEqual(plugin._meta.db_table, 'one_thing_testpluginmodel3')
        self.assertEqual(plugin._meta.app_label, 'one_thing')

    def test_meta_options_custom_db_table(self):
        ''' make sure custom database table names are OK. '''

        plugin = TestPlugin4.model
        self.assertEqual(plugin._meta.db_table, 'or_another_4')
        self.assertEqual(plugin._meta.app_label, 'meta')

    def test_meta_options_custom_both(self):
        ''' We should be able to customise app_label and db_table together '''

        plugin = TestPlugin5.model
        self.assertEqual(plugin._meta.db_table, 'or_another_5')
        self.assertEqual(plugin._meta.app_label, 'one_thing')


class LinkPluginTestCase(PluginsTestBaseCase):
    def test_does_not_verify_existance_of_url(self):
        form = LinkForm(
            {'name': 'Linkname', 'url': 'http://www.nonexistant.test'})
        self.assertTrue(form.is_valid())

    def test_opens_in_same_window_by_default(self):
        """Could not figure out how to render this plugin

        Checking only for the values in the model"""
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test'})
        link = form.save()
        self.assertEqual(link.target, '')

    def test_open_in_blank_window(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': '_blank'})
        link = form.save()
        self.assertEqual(link.target, '_blank')

    def test_open_in_parent_window(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': '_parent'})
        link = form.save()
        self.assertEqual(link.target, '_parent')

    def test_open_in_top_window(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': '_top'})
        link = form.save()
        self.assertEqual(link.target, '_top')

    def test_open_in_nothing_else(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': 'artificial'})
        self.assertFalse(form.is_valid())


class NoDatabasePluginTests(TestCase):
    def test_render_meta_is_unique(self):
        text = Text()
        link = Link()
        self.assertNotEqual(id(text._render_meta), id(link._render_meta))

    def test_render_meta_does_not_leak(self):
        text = Text()
        link = Link()

        text._render_meta.text_enabled = False
        link._render_meta.text_enabled = False

        self.assertFalse(text._render_meta.text_enabled)
        self.assertFalse(link._render_meta.text_enabled)

        link._render_meta.text_enabled = True

        self.assertFalse(text._render_meta.text_enabled)
        self.assertTrue(link._render_meta.text_enabled)

    def test_db_table_hack(self):
        # Plugin models has been moved away due to the Django 1.7 AppConfig
        from cms.test_utils.project.bunch_of_plugins.models import TestPlugin1
        self.assertEqual(TestPlugin1._meta.db_table, 'bunch_of_plugins_testplugin1')

    def test_db_table_hack_with_mixin(self):
        # Plugin models has been moved away due to the Django 1.7 AppConfig
        from cms.test_utils.project.bunch_of_plugins.models import TestPlugin2
        self.assertEqual(TestPlugin2._meta.db_table, 'bunch_of_plugins_testplugin2')

    def test_pickle(self):
        text = Text()
        text.__reduce__()


class PicturePluginTests(PluginsTestBaseCase):
    def test_link_or_page(self):
        """Test a validator: you can enter a url or a page_link, but not both."""

        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        picture = Picture(url="test")
        # Note: don't call full_clean as it will check ALL fields - including
        # the image, which we haven't defined. Call clean() instead which
        # just validates the url and page_link fields.
        picture.clean()

        picture.page_link = page
        picture.url = None
        picture.clean()

        picture.url = "test"
        self.assertRaises(ValidationError, picture.clean)


class SimplePluginTests(TestCase):
    def test_simple_naming(self):
        class MyPlugin(CMSPluginBase):
            render_template = 'base.html'

        self.assertEqual(MyPlugin.name, 'My Plugin')

    def test_simple_context(self):
        class MyPlugin(CMSPluginBase):
            render_template = 'base.html'

        plugin = MyPlugin(ArticlePluginModel, admin.site)
        context = {}
        out_context = plugin.render(context, 1, 2)
        self.assertEqual(out_context['instance'], 1)
        self.assertEqual(out_context['placeholder'], 2)
        self.assertIs(out_context, context)


class BrokenPluginTests(TestCase):
    def test_import_broken_plugin(self):
        """
        If there is an import error in the actual cms_plugin file it should
        raise the ImportError rather than silently swallowing it -
        in opposition to the ImportError if the file 'cms_plugins.py' doesn't
        exist.
        """
        new_apps = ['cms.test_utils.project.brokenpluginapp']
        with self.settings(INSTALLED_APPS=new_apps):
            plugin_pool.discovered = False
            self.assertRaises(ImportError, plugin_pool.discover_plugins)


class MTIPluginsTestCase(PluginsTestBaseCase):
    def test_add_edit_plugin(self):
        from cms.test_utils.project.mti_pluginapp.models import TestPluginBetaModel

        """
        Test that we can instantiate and use a MTI plugin
        """

        # Create a page
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # Add the MTI plugin
        plugin_data = {
            'plugin_type': "TestPluginBeta",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEqual(response.status_code, 200)
        plugin_id = self.get_response_pk(response)
        self.assertEqual(plugin_id, CMSPlugin.objects.all()[0].pk)

        # Test we can open the change form for the MTI plugin
        edit_url = "%s%s/" % (URL_CMS_PLUGIN_EDIT, plugin_id)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Edit the MTI plugin
        data = {
            "alpha": "ALPHA",
            "beta": "BETA"
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)

        # Test that the change was properly stored in the DB
        plugin_model = TestPluginBetaModel.objects.all()[0]
        self.assertEqual("ALPHA", plugin_model.alpha)
        self.assertEqual("BETA", plugin_model.beta)
