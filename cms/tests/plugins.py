# -*- coding: utf-8 -*-
from __future__ import with_statement
import datetime
import json
from cms import api

from cms.api import create_page, publish_page, add_plugin
from cms.constants import PLUGIN_MOVE_ACTION, PLUGIN_COPY_ACTION
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.models import Page, Placeholder
from cms.models.pluginmodel import CMSPlugin, PluginModelBase
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.test_utils.project.placeholderapp.cms_plugins import EmptyPlugin
from cms.test_utils.project.pluginapp.plugins.validation.cms_plugins import NonExisitngRenderTemplate, NoSubPluginRender, NoRender, NoRenderButChildren, DynTemplate
from djangocms_googlemap.models import GoogleMap
from djangocms_inherit.cms_plugins import InheritPagePlaceholderPlugin
from cms.utils.plugins import get_plugins_for_page
from djangocms_file.models import File
from djangocms_inherit.models import InheritPagePlaceholder
from djangocms_link.forms import LinkForm
from djangocms_link.models import Link
from djangocms_picture.models import Picture
from cms.toolbar.toolbar import CMSToolbar
from djangocms_text_ckeditor.models import Text
from djangocms_text_ckeditor.utils import plugin_tags_to_id_list
from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import Article, Section, ArticlePluginModel
from cms.test_utils.project.pluginapp.plugins.meta.cms_plugins import TestPlugin, TestPlugin2, TestPlugin3, TestPlugin4, TestPlugin5
from cms.test_utils.testcases import CMSTestCase, URL_CMS_PAGE, URL_CMS_PLUGIN_MOVE, URL_CMS_PAGE_ADD, \
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT, URL_CMS_PAGE_CHANGE, URL_CMS_PLUGIN_REMOVE, URL_CMS_PAGE_PUBLISH
from cms.sitemaps.cms_sitemap import CMSSitemap
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.copy_plugins import copy_plugins_to
from django import http
from django.utils import timezone
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.forms.widgets import Media
from django.test.testcases import TestCase
import os


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
        from django.conf.urls import patterns, url
        return patterns('',
            url(r'^testview/$', admin.site.admin_view(self._test_view), name='dumbfixtureplugin'),
        )
plugin_pool.register_plugin(DumbFixturePluginWithUrls)


class PluginsTestBaseCase(CMSTestCase):
    def setUp(self):
        self.super_user = User(username="test", is_staff=True, is_active=True, is_superuser=True)
        self.super_user.set_password("test")
        self.super_user.save()

        self.slave = User(username="slave", is_staff=True, is_active=True, is_superuser=False)
        self.slave.set_password("slave")
        self.slave.save()

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
        self.assertEquals(response.status_code, 200)
        created_plugin_id = self.get_response_pk(response)
        self.assertEquals(created_plugin_id, CMSPlugin.objects.all()[0].pk)
        return created_plugin_id

    def _edit_text_plugin(self, plugin_id, text):
        edit_url = "%s%s/" % (URL_CMS_PLUGIN_EDIT, plugin_id)
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body": text
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.get(pk=plugin_id)
        return txt

    def test_add_edit_plugin(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        created_plugin_id = self._create_text_plugin_on_page(page)
        # now edit the plugin
        txt = self._edit_text_plugin(created_plugin_id, "Hello World")
        self.assertEquals("Hello World", txt.body)
        # edit body, but click cancel button
        data = {
            "body": "Hello World!!",
            "_cancel": True,
        }
        edit_url = '%s%d/' % (URL_CMS_PLUGIN_EDIT, created_plugin_id)
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals("Hello World", txt.body)

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
        txt = self._edit_text_plugin(created_plugin_id, "Hello World")
        page = Page.objects.all()[0]
        self.assertEqual(page.is_dirty('en'), True)


    def test_plugin_order(self):
        """
        Test that plugin position is saved after creation
        """
        page_en = create_page("PluginOrderPage", "col_two.html", "en",
                              slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")

        # We check created objects and objects from the DB to be sure the position value
        # has been saved correctly
        text_plugin_1 = add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        text_plugin_2 = add_plugin(ph_en, "TextPlugin", "en", body="I'm the second")
        db_plugin_1 = CMSPlugin.objects.get(pk=text_plugin_1.pk)
        db_plugin_2 = CMSPlugin.objects.get(pk=text_plugin_2.pk)

        with SettingsOverride(CMS_PERMISSION=False):
            self.assertEqual(text_plugin_1.position, 0)
            self.assertEqual(db_plugin_1.position, 0)
            self.assertEqual(text_plugin_2.position, 1)
            self.assertEqual(db_plugin_2.position, 1)
            ## Finally we render the placeholder to test the actual content
            rendered_placeholder = ph_en.render(self.get_context(page_en.get_absolute_url(), page=page_en), None)
            self.assertEquals(rendered_placeholder, "I'm the firstI'm the second")

    def test_add_cancel_plugin(self):
        """
        Test that you can cancel a new plugin before editing and 
        that the plugin is removed.
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        pk = CMSPlugin.objects.all()[0].pk
        expected = {
            "url": "/en/admin/cms/page/edit-plugin/%s/" % pk,
            "breadcrumb": [
                {
                    "url": "/en/admin/cms/page/edit-plugin/%s/" % pk,
                    "title": "Text"
                }
            ],
            'delete': '/en/admin/cms/page/delete-plugin/%s/' % pk
        }
        output = json.loads(response.content.decode('utf8'))
        self.assertEquals(output, expected)
        # now click cancel instead of editing
        response = self.client.get(output['url'])
        self.assertEquals(response.status_code, 200)
        data = {
            "body": "Hello World",
            "_cancel": True,
        }
        response = self.client.post(output['url'], data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(0, Text.objects.count())

    def test_extract_images_from_text(self):
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + "%s/" % CMSPlugin.objects.all()[0].pk
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body": """<p>
    sada dadad asdas dsasd<img alt="" src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQUFBAYFBQUHBgYHCQ8KCQgICRMNDgsPFhMXFxYTFRUYGyMeGBohGhUVHikfISQlJygnGB0rLismLiMmJyb/2wBDAQYHBwkICRIKChImGRUZJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJib/wgARCAHgAooDASIAAhEBAxEB/8QAGwABAAIDAQEAAAAAAAAAAAAAAAMEAQIFBgf/xAAaAQEBAAMBAQAAAAAAAAAAAAAAAQIDBAUG/9oADAMBAAIQAxAAAAH5SAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAyMM5MJbOzCivxZ41W+mnZgSgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZOjZz7frOt1c/jLXqd+zl829HHt1cF29dungxdyuvC53o6Ojp4C5T8n0cDXmAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2x6HKY9lct+p51baV0aNK80eN0zvBnjFJlljFUtRnM53Y5tw5XL7XP5PQ5rOPI7wAAABkw2yaNxo2wYAAAAAAAAAAAAAAAAAAAAAAJjo/ROV6z0eLGZtOrkrw2NbjWgsxZNoGbI4L1KzNOzWjSldgzw49DqcvV08vTbXw/VCUDLNha0vX6zq4XS7Wrtry75b9NLGVoVe3lr8nT9waPnsfu+a5fLOpRc0DOGIAAAAAAAAAAAAAAAAAGfRcL6Vv09y9rt6Xn4jzVuNqDeJIoIo9mOMYq5yzUzlM7wR1XjtVLhV4vT4vD3VMZx5XpZJiG30Og7ql3Or0Zs18t0qETbQYJ818ljaqLslDY6G/O2OjXhlY8nkez0cfgtfYchw8ZPA58BAAAAAAAAAAAAAABsdz6l5D3vp+ftFvQ26dZKkW3XYg2hsj01q5TSaOvYlr2rJK00SuXb5qUeXbz43t86TpWOb1KXS0y659YNnRvnSQb4G22hctdTdjBnDJpnOBtGSbeqW7Lz81088/eJqF6Zq8vS9vE4fEPR8pxUEmjVgAAAAAAAAAAAGbtL0uePt+9o9fytKW1bZhJQzrljvBHmtLnOwlylXksKkJc1pV8crXPUuPvhtUrnl+7LtpmelJnTNy330JNnG5naHddtddTbGuTfeLZc403qbTCI9k1Vtd8GuMYSTeDZbEtOQuy8/aOm586a8zuSOfxtX3Vdx+Ldyg46LfVrwAAAAAAAADb6J4L6r183fp2eZ6Pn6094duqGCKBbEEdW49GCrphss14IufsxpDpo35jxHy9LTOmrPW5RtY9NpjL1Ns4XKRjBvmLKT66l3xjQl0F21CXSSJZ48akskKtZNNpr0zviatdJNoj1khy2S7Vt7nPmDZlamobnSm5csdFUlSLndrdo8jU9vXcvinp+a5OUnhc+oAAAABk631j539J9Lgc23yu7jj0zHljFx7NPDNFJa8706DrzcfZx6vY5etUgmiw2Q6765SOKWPPDSWLMvQ3rTz1t2ubt22j2VnGCTXC2ePOF2y0N850s31bTVnEthpqS3JZx1FuNyQ6WedZx9quuG7fGuLju0wW5+au7tS8Ga9Xa25k7pv70t227vR2XoZ5+y9Dbm7Ldpb7tXG5/sY5weNx3OReCIMQAG2sx7r2nn/Qez5XNoXub0aI62YcNkdrt7eJ7PMsSWtapjpa2cih6GoeMpeu8/jnzo54sdsUUseWMeu2LjJZpTTptZh2dkuYjOXMOCfEEbXY0r6ue1its1WEezDPW5HTa7k8E+WuaXWUxHajIfK+j8ZMsGJWMrMBAGWVZJnnbQs+9ZMrKsW5ioZWs1ssun1fL3W/1nMz0suvwkXf4DxMC6wM3KfYyx+k3oJPc8jm87o0spF0+d7XyvVrb2tuPbyY+xRrTFqc41e7Ac3kd2mePo9vjY5wR7aTZrrvrcddpett18ef01ju5PNz991cnAi9FHHnIPR0tHTxsdrQ4+OlHr20998cu/Fqq1Z96etYY2pa26XqnL83Mt4M4mTGcIFmGcIMjLMzBWRQhkDJcmRlmOn2/Od6+nV8v63yWXFqLxAZ9L5r2m7V7WKen7Xk1op6unq6/pa1nyPRzHdp4Nq+YDFrycsvTrcqudGpzKUsnB6lfKcXX0Xb6dXke52Ze3jryWJerkrZuy2c3HWwciTqQHN5HqeZjeTH36rLhRdKBOVi9vMuXr0odeyDoVqvL1T821pLS0uQadsQ5OnATAsYzhjnOMsmSZMkoDOMqzjIyyM52lxnIn9D570rur+Q9d5DPm1F4gNvfeE+i9fN6CnZp+r5q/wA/ted6vpIq1bz99iPyvhJl9H+fcjOOYzlMZ6fR6ebhdrpWezlhm6GnTojsdiHLVy7VbtlOafOFry2LOvKhm4mdWn0aueuhy+1X3YUqvR5uUr0OpXuNel0auNjr2YbNNZYmVbSxjDdUhtRYbufrLF4vpMZxhkxnFgJnOMzNklGTGQGVZxsNsbQznK4zjKz+j896DL06flPQefvn4F4wLP0j5/8ASPR4Z60z0OGrx7PiPI9jsc+DPB2GZbIZfSdr0OHhdOSD0vNmz0tM8I3TrSyZkjls2I2F4/f51tLGm1PXn3d6dvm6cb6arXhsVd2mnnON2mjTuR7Mebmzzs8Yo5dGNBNolfE8Myi0kjx2xRzRzbQr2K/i+qxnGnNjOLGcbDJjmyKZRhlQGdtd5c5ZGWZcb4sXKbsczqbPX89yblOeHgXSMnb+g+O9v7HlwbYg6dHmfOXaPg+5vv0PTWcf0um3qeZprX7nTzU63RSzIrcWaU0WNuQ24Ma3oWbJsVZJl0a8O2OS5WhixNDVrqc9ULlKLXZrs0JqWc3qT6XGOtPrZXgs1bjDrvpJDFNHhvjhlqzdSiY8L1ssMMmMkZxsyZJkyQZyuGw1bSEdn03TuvyVj0kdnkqvt+avA6K9l61adXb/ADUWcPn8BM7aW7Pa+ipWfd8eDk3Iq8N6Tr2Oboi2kt9XLV6O0xVW9McobkOUq2cw1Zlh0xa7aQ2b7VlT60Y7OnjlynTiiry3dNayXNOdvZY3q7VtBrEkmsUdmdYY7jNDthNI5YVjiUNHVY52kXnekxlxdOMbZs1xJrLjbGyskyzltLjZKRO16C4+I9hD2Lhs22ywrR2YFr8+xM9LlWMW3pRcL0fj3FQwPHAz2uL17PqfO6T3fH85a6WueuDa1YmVCW5jG7ab6S6SY0JaitZYir1av68uOOzW5MR13D0juQcfSO5t58egcId2Pk7WdaTj711N+XiXp6cuI60fFrR3o/O1tWz09bzkejf26PPc/RJpjPP0bZZx2Y233mUW1je7qkd+Mp5k0mltv20qdfo2Lr8/2JZLJbda1ZPyrlQk3p15utwVbr1Ibk1W9dGS3VKni/Q+aeNgOMBJGPa+w+OWt+n6/t8oxu1fVOd82hxy+kVvnmsvu6vjGGXqq/ncY5duLlMcujFTY2zpAJtY0smNBs1GzUbNRu0G7QbtBtjAywM4AABkJJoLmPRvPtJl62NpJrvh2n2kqw9HDGr0K2MfM6U1GzeGzNVsJZsV97Z61ejO+eHrU76t7mdHNsdnj9yObUtcpr8vz99J8/gXEAAAAAAAAAAAAAAAAAAAAAAAACTqcvrz0Zdm2Xpz2Y5oxtYysONxFHb2OXnpQY8m1jmSuC/iKXL1bVLrV26/PyOsc7q1oU59mxRWbx3o/DTz6+C+SAAAAAAAAAAAAAAAAAAAAAAAAABJ2OP2Z32JMb5enNPBIwsyxJLdilZb9sbZWGncgIsWKiXYJryyTc2+cbpSwp1OF2ITSjY5ScbzVuo8HAaQAAAAAAAAAAAAAAAAAAAAAAAAANu9wO9Ou5lm+xPnCpZ6ssXJo92aTSuY20nNIZskfQ5N4s5zEdTldrz50MT0jTy/o/AuGnqPHAAAAAAAAAAAAAAAAAAAAAAAAAAAz1OVYmz0+dMvdNdrsms1ZCzZqyrvDnQxZ595MT0tlhtWeQnoqeJls5i3IIpKCczyV2i8HAaAAAAAAAAAAAAAAAAAAAAAAAAAAAGcD01vh9yezG21y6t5IdplPNTkJpItSO3XEmIZDqU47qxTULxvjEZN5/qeMcNTUeOAAAAAAAAAAAAAAAAAAAAAAAAAAAABJ6TzHSnT2dYZb7MuuMM9pK8ib7V91vVMwE0sUZ0LFOQn3q21xpvzWPP87YrvAwGoAAAAAAAAAAAAAAAAAAAAAAAAAAAADO2o7Frh9TH177G2Xdqzg1MptjTZZIs4SzJVmXeetuWvM2uA8zXA80AAAAAAAAAAAAAAAAAAAAAAAAAAAAAADNqrmbPQT8fq33ZGuWzVnUywMtSb7xRpZ59WhPN20L52AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAb9HmJv9JJ5629Lq4pyXdMrV2PQh5ldy36UZwsDUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAzgZYGWAAAAAAAAAAB/8QALxAAAgIBAwMCBQUBAQADAAAAAQIAAxEEEiEQIjEFExQgIzJBMDNAQlBgJENwgP/aAAgBAQABBQL/APVeIEJgoM9mGowqR/xABMSh2iaMxdGs+FWfDpPZxNkKwpGrj14/4ajTM5o0IEGnVZ7QyEhTjZCgMKx6uDXGWOssT/gwMzSaQtKNNtAAgGY6cZGwgQjbCuLAJ2gtgG0RxHEsXH/BaHS7jRUEUqRNuRjMP28BzuWAb6n27G5jeGIZHAMsEaWj9baZtMwf9HRUGx9NSEVBkHsLY3HkqXJTHukAkArqWU7fd3U7qzC1Yd27XHa8sh/RVGaV6RmiaIQaJABpa58KkOlSHRKY+hEbRmNp3EKMP8utdzenUbVRcQjbDkTZtXcbRn3BaAQLVIvxMrZKcYRwBayZ4lmDHlvg/OtLGVabmupQBtELT3JvnuTfBZN+YNsKKY+nQy3RCPpGEath/kem0bm06bV+yZ2DiCwBtRGHbvdIy1s6lWT+q/uDixyuSTk7pbLj81dLNKtOBMYIM3QtMkzM3TM3GZM3TdA83wNO0x6EZbdHLNOywgj/ABKl3P6bRhRjHtlInhj7ZfYqqyge4abN1mSjM2XEqfcg277t2N5IYbY5lxlp+RELSqgQACbpmE9MzmeIfBnI6ZmZmbpum6B5uhVWlmmUy3S4jVsP8L02rdZphtQ4wxwGISxx7kU9qbVmoKqpLOO4Nb99WRP7YzB2h27GMuMcGYMFbGJQYiKsziZ6kzmZ6DOB0/HTPGeczMBm6BoGgacGPWpj6UGPpmEZGH84cn0imBGEzksVyRXF9z3C+1rd+0Wo8AtWO3uR+Qm6YOM8sY/2ucR25UQAQYm6EzPycznoTichx4ZpxkjEOZ46fnpmZm6Bpum6BpwY9KtLNJH07LCpH8vSpvs9PrwucRu8M8yLK3yUGwxTiIQAuxhur3/1RxGfafyWjWdrtD5Xx8q8keZuOPz/AGP2HmDwD2zOYWi/a3APMGMdczMBgMBgaB4GhVWj6ZWlmjj0OsKkfyPS68tUmK3MLDJt7s+3YzsrJYqyxl3fYWxksJu7VYKzvDZGeF475n5X5czMyMA4biZyPwsGQD58TOBjPRvtbBWvG3apnhiIOeogmZmZgaBoGmQYyqZbp0YWaSPQwhUj+IPPo9XH2hnBhYR23S1leE+2WbBLYgOY0zyzGb5vhYmEzMM/KfLjkQeM8EzMPPT8ZzBzD5HgGE8V9N0Y4bOYsPEPheueuYGgaBoGnmFFMfTKY+jj6ZhDWw/g0DNnpyYRmzLWWNYGDEtLSVgMc8M0VuXabuGPU9T0T5fM8dMwQHkefyemen4xBPHVoAZtOSpgG4BZtIjbRA6mZ65mYGgaB4Hm6bp2mNUpj6UGPpSI1TD9bQJus0oKI5VzY5SFVx2kE7puwWfPUKWntRgOh6mHosH6OecZEPgQ+B8ogQwJjpiGJayF73aZ67jFuInvLEdT0BmZmbpum6bpum6ZBjIpD6YGWaUiMhH6fpNeWXKo5RpYefwxG025LDJCkxdO5nw4mzAdCZYhEzD1PURT+gIYDPyJ+em6cwJAiwCATExMTWNsr/RFjRb57ymKwMzAZmbpum6bpvgsikNHpVpdpCIylf0BPSEjZAtYEZmSpZsRK8z2oi4m2bJsjJLK5dXg/IeqmA/oZm6b57pnuGbzMmDysEExBCJiYmtfdd+ruMFjie8095p7rT3p7xnume60rvldk4YajTgrYpU/NWMv6WmFcywiEy5uEBsZKMB6cwLiKs2wrCsZZdVmW14JEPQ/IDM9MzMzMzMJmfkHWk5UQQQTExNXd7NP8iq3ErsmczX1j59KM26AAVucS3Bg5jzQUcBJsj1wCAQiERhGEvrlghh+bMVXaLpnMGknw0NENJmye3NhmD8tB5EEEEWarUJQttjWv/J0zRGmr+w/N6cubKOEOJcMxPurU2WqmFxMRlzGWVLulqLtaGNLBmaheXh+RK3eVensYmlqSbQJjE2me3mGqPTPb52EtYozsjLNsx0BwynIEE3Kku9QChmLt/Kp81eNV9jefl9KQlgdqMytHmcT02vLgRhM4JjCA7TlSjQxo5Ev5lo61aS2yU6OtIqTbNsxNpmDNsFYltMtQiOhEtVSbVAe0TExxthSU2bJ7qAWalzGJaEfzKfvpJE1f2Hz8vpCznDEQjIfM09ftUg4nlbIJbatQb1Og2HX04b1CqHXIY+sEN5aEw02WRNBKtNXXFHODAmIAIFntnAr4KgTZmKO4/tOF3un/larKWJgNyWG2bY64ghWFZthExCP5dX3UzXfafPyCelL2mPnJxPTahbqra9oNYZM4ltoE1Pqenpmu1tmpf5Kq7LDXpSJVSghXFiiBIsFJNzVYY1BQAIK+djmFO3AMevbFXdPbPuDPstytbDaRzYAU/AGSV2sYQDMckdGEP8AKp+6nxrj2fKnLemgbW24yYT26MFKvfaG4KNZ6tTUNRrL7m6jmV6K5pXpaUe8EIgJiKu4jdelaopG56OGqTi9QFr3Mqp3lZt72TaG8MkrB3WRU3KOIBiNxEhwrcSw5nkRo3Qxv5VPmo4muPHy0DNmiwKzDmXMEpb1u8rb6jq7I1tjfJXW9jUemSsVJKVY2Ov1iu6nSrwRixcfEExVBCZW9SEGpXFWl8f/ACHdu/ufBxjHYTsexZXxbcuLDyj8qQVS0BkExmLCMQ9TH/kqMlPKfbrTz8ujGbNMpWs56eqNjSfJXW1jaf0wT6da2lvbq7yUxZYmL60xVoPD5LNxa6H26yQLlBioWRWHs6btZWzqNwELiM20FuN0uz7ZfsK4pvlajA8c7ONhXuPEbmH5DLP5A5g4lc8JqTl/l9OXvrHZzMz1hznoASdPoC0rRKktsgXK7MzSrhk/cvE/umEYp3ahSyVHer42OPoV8NYiAqgj7gw5BtwTtzvXdYWF2cr/AFYg2t+2e1yMRfuCxxmoznoehjRzz/BEWqwyrS2PDoWj6e1OlQzGTKV5lhwlhy3y+lpzjtJxCZrbPc1M0+keyU010jdwgYxlZLvtrpXutr+pQ29sDb9lmo4Y9yDOKW+H1FrbXucIjsrBbw8tPbqG9ylHba9gsVbDXM2ZZ/qo3eWyzcNDjbZPwuCZzgww9DLDgfwVUs2n0iVzHQxQrC2pXlaissuUTk6xsKflHn0xMK0YzWXe3SiM50ukCRehrLMol9e8V+c7GUZH7d7jsPeO3dVa1U7laxMlbEYs5C+7lLMWBHQsPZEqIVnNbLYd6q7NX9xZyLc7UfuM4hMz2gwnkmHoYYxxLGz/AAVUs2koWtAOD0I6XORPazAcqMTWt82nXdZok2pYY74hrS1UqVBtjDilBtUdzTwEH1bkzXSZjeoY7GG4sx3X9613fTfg2Nk2MdynayWbQTi13zGOCzbgHZamLe7yYxCvY525mcTOZzCTPMx0MMZwI90Zif11UmabRM8+Box8B7VoHaOhj8DcxlteUo3Kcd7YC6psv8vpq5trVfbu4JQ5rWVjcSMyuvmoZgGWUblXJrcYY/dgJd/a3uhaO3aXJLMdpbtZ+CwILYnuHJcmByAzduTM9rHMzPz0ImBDDiEie4ojXrG1Aj3kxnJ/VAzKdKzz4FMLosNVWqRBkmXutlWcQdLLFWAGw21lDUQUvQ1W7QZqnwlhy3y+nPtt0p3JamSa8BV4NfaiZgH02HJ+8HtJVbN64Niyy4Rr13NesOoXb8SIdUJ8UJ8SJ8SJ8SJ8QJ8QJ8QJ8TPiRPiRPiFnvrPfWfErPiVh1Sw6tYdYIdZG1TQ3sZ7jTcfnxAIFmybIUhUzEVCZp6QJXiZ6LF8/iOJv2gs9ksqwulPI5DfSfVLlFG2a+z50Yq2h9QxE1dbB7a3i21ifFVhfjlQH1BQF9TxD6niH1LhvUjD6g0OueHWWQ6qww6iye889x5vab2m4zJmTMzMzMzMyZuM3GbjNxmTM/qiAQCYmIFm2e2IahKgFixTMwQQQQywhRjdK27lQPXg0225zqE36ZvqUscJq33P84OIl9iz42yHWWQ6mww2uZvaZP+OIggHQQCYmJiYmJyIlgPQGLBC4WPazROXQcX17YjfRtq92lbT7dZHtqCs1r4Vzlv8AVXynjog6ATExOIYYyxbSsVsxWhuz0VcqjbbKsEYBW76UobFGwq1bbTZ2H1CzJ/1l8p46J1AhmJtm3o6AwV7TjipOB91fjVVSiyZ+r6mOxP29Wpdc7pqn2pe+5/8AWWV+BBBBBM4ACgKmZiYz0PJWvJtxmgSzsaohkxuRlNNytzgW6VC1ZvI9uwDdrreP9dfNfQQdFHCT87jCTgniw4iRAS13D0mahARpsiZKv6goKU+Kv2XQWVVdyWtsXUPuf/XHmscCfmDozZiDC4j+Lu0PmKO1f3NQv09PzLG5tTtDTUYenSntLe2oYe26mt9dZiH/AGdKcovkcuYeCDFG6Zw2cKnc7Hc1nESJybxk6Ru0n62drjstUBq8Gt+21KsbdQdlepfc3+zo258TwfM5MSVnkGOSpsbv/tqDkrwtP3Wndd+1aD9QqWrH1Gps7b13SslHmtv+kef9qptr+RBPyngZCVeQcjj3FOBaZV5oGGLYsar36a270eP964IrbdOXrtfA1T73/wBvStur/Bn4HhzFbE+1l/bZSFccflW77f3dM+Jq1CW5yofa/wBjqSrOdjeoWw8/7mifaxwOojT8WH6YP0yTtc/+cNPFnmVHMtG5KiwFoGwHtGVlj4r1D7m/3EOGRt6FoIsY934J7QT7bnvTulPg/bSeCvNRyEw4XM5WM3brLeP97TWYhixY0MzE5QnLDAYdreYkz2E8Ke0ENN2Ze2wWtub/AHgcFHyoMEbzF4g+6HmNyoOVzhge1DFOCDy7cau3J/4CtsStoOvlTDPBPjwfIHj8jk5l92Ixyf8AgUaI2R+IOOgn4/GehghMuuxGYk/8HS8U8dD82YzgSy7MJz/woOJVbAwPzZjWCPdCxP8AxK2MIuogvWe6sNojXRrTCxP/ANb/AP/EACoRAAIBAwMCBgIDAQAAAAAAAAECAAMEERASMRMgISIwQEFRUFIUMkJg/9oACAEDAQE/Af8Amy6iCop/CvXAhuHjVXMOZkiUqxEVt34EnEqVS0AzMQ68GUX/AANepnyiY7cwyj2AE8RLV25i2ajmCgg+J0U+obamY1kPiNausKkc+0qvtXTPcZbJnx0xmUrQt4tFoqvHoFFbmPaKeI9s6zGPY1juaE9+My1okiLZfZlOgqeq9FH5j2f6xqLrz6zHAzM/Mz3BSZSo/Jlr4exxmPbo0ezI/rGpMvPp1zhcQzmZ0VC3ES0PzFtPuCkqzEtzhvUNRV5MNxTHzBXWCosDA8dmAY1ujRrL9Y1vUX4mMd9w3mh0SmXOBKdmF/tAEXibhqYpwYjZHeWAhroI14g4lS6Z+ITnTMzNxi3NRYl5+wguEM3rNwmdHpI/MqWf6xkK89tQ5Y6U6ZcxFFMYhOdVbspPiB5vE6ghrgRq7Q1WM3GN2DtGodp1GnVf7nWf7lO4P+oyLUEqJsbGrHAmYBkyku3uU6tUVOY9+f8AMa5qt8xbir9z+S0/ktBcwVVMyDCNMetbt4S8Hm1q/wBDpRT57MTExo9yiypdFuISTz2ZmZunUgqnmLc5nWi1M9o9GgDiXZ82twcJpTWYgWAQsBHuUWNeE8RqzGYg0C5myEa4mIIDA0UxPEerbjyy7Pn1ujwNLU5XWtc48FjVGbmYmNRPmAzwh7swQSl/XUeiBkxRtWVzlzrXOX0orsSVK6JKlwzzmY7siZ8ZmM2ZnsOgiDJijAxqO7fN8DyhT8uZUOFh8Tq5y0QjOTHui3gJzoO7MzM6Z1zM6CU6bNxKVHb4nTExB2bhGbQDMoW2DltLtsLjU8RhMTEx2YM2tNrfU6b/AFOlU+p0qn1OlU+p03+p03+p02+p0n+p0XPxBauYtmP9GLQRfiDTEFFz8Q0HmCITibjM51p0mqcSjbhOdbpstjsekrT+OJ/HWdBZ0UnTX6m0TA9hTXecCU6KpqyK0rW2PEQjGgBPEpWZJ80VAnGtRtqxzk593Z6Z7KtuGgtmJlKktMeHbePgY95aHx1DHPZjtJwMytU3vn3lqfNpibfRu6mFx72k21op9InErVN7e+oPuSD0bqptXHv7epsaL6DNtGZVfe2fwFrU3DHbnW7rf5H4Gm5Q5lNw4z2lgOZWuvhZz+CpVmpxLtDzBWQ/MNdBHvP1j1Wfn8l//8QALBEAAQMCBAUDBQEBAAAAAAAAAQACEQMEEBIgMRMhMEBRFEFQIjJCUmFwYP/aAAgBAgEBPwH/AJttNztkaDwiCN/hKdsXboWzAm0WBABQqlIOCqUyw/AtBcYCpUQzdF0KShorszN+Bt6eUZipnTGD9kd+/o087kcAPdAabmpAj4Ci3IxNE4RplXDszu/Y3M6F/EBqJVWtGyPf2zfqlNGEYFwG6dcBOu42Tq7nKetKzKewtm/Qm4OeGCSql3+qdVc7dc8R2kqVPSpCGgYPeGhVKhedBHRlT27BLkAiYCuHzy1HFtJz9kyz/ZC3pj2RoU/C9O1elYUbTwnUHNRaR2I0UBLxhVdyT3ZjjKlSt9ky1e7dU7Vrd0AApUqcIULKnUgU61Xpk+iQOsNFqJfhXfhOAYTsmWj3Jlm0fchTaFmTjCzcpTqizppU88Z0OEhPEO6o0Wg5E4XnJ2EKjazzcmsDVKnD25J3ML8SERBUFNnAa6339jbiGYV353qnbveqVu1mE4BCVHNQVB2USFlTWQoQ1OMCU92Z09GFChDbQEwQ1OmOSZatbzK2wOiFChQoQHQfVa3dVrjPyHQhAdBu6aVKJU6JCzNWdvlcVnlcan5XGp+VxqflcVnlcRnlcRnlcVnlGvTHujdsCdeH8QnXFRyOuNI/utlZzV6r+L1Lkbl6471xX+Vnd5UlT2EaNvioQP8AuI/wr//EADsQAAIBAwIEAwYFAgUEAwAAAAABEQIhMRJBECJRYQMgcTAyQEJQgRNSYJGxYqEjcoCSwQQzgtGi4fD/2gAIAQEABj8C/wBfVzBMEQY/R0YZ3JSwSjuYJ4R+hpZg07ml2Ypqh7didN9zXTOjc5sMU/MjOB/lf9j7Cq/QssVjEo/MvzF3TTXTv1Nap5kKun50aW+SrYdTfulPiW73JomO41gpatGT+PgcGPqWDBAk1y79ixzSnmlk2oqX9x+Hq966LV8+49VPvorop5qM+hTXeUbDpXzGm1ifaY4XJ4Y4YLFjBj6XAnwlJP0LxpLK2z3RZaa12NVELxKco/Hp9/8ALSKqKelUiqpc6XeC0v8AqkrphWeRqq8WQuotP3LezuY9ngtwx9Ili37E0+7uamuUnUtL/sfheI7dep+ItsLsUeN4Vmt+pzUcrz1HTVeirDWxosoUXJ8NcjzT0Y/6iKsMq1XOUh+xuRxgRn2V+FvoyQmRVTcmiXS/lkm+l7F6Yor26FMQ9N+5qdUraR0TKd12H+E+84Qr0zj1HmaXNi9h81SewoWDBqdyfaP4K30OTAnldifDafU1/K8lVMynmr/0OnQnG+7Pw663G1tiaVzK6gbVTneegn8rclNW76MssCZ6kbee/m/uStzP2MO5Hkn2918epLVFkqa9zVEVLJyzD+TqPwcKm69B0Uv7s/Epami57nM10E/eSyjMOT0OSqGbcI9oiy2FzW7FiehPUUsUQthXO3DBP0uIk5f9rOV3J0zWspn+HbV/8RNVR4nhlLdcVfyNVc0D02W5qn1Ha6xwvwnUZO459hBAxM/9D7j6lj3uGmfQ0mnhcTWDPtrfFSf8o5nPdHK+b+RQ/eyhpb4JpWqc9hwtycyTk1eG4kzeeEvhd+zT6ErJ6kEPJm6GzBkfB1IXCOHQgle2sviEcrh9D8tRz0rUVKm05KZmVZsaoZq68Ls6H/I/bwNSKLwKok9TuRBDI888I+Btwx8Chcp1LrS1uaWr9To1iCrujPw+l+S3myW8+Z43qRn4DHt1FzuPVekmlSWs6SMDXksX+icp09DPkvfhZ+2t7Xrwiq6NH9xszHCEi9uFl9Ejd+yyXXDPtLF/Yos5LovdHcyTsdEW+Nz7Jxim3tsmfJjyX42RHnRkvScjMX6ErYVhfSH+Z4+Jh8Z86Fcuv2JpyZPU1v4SyLmeGfZR5ruatkaq3f6JdFnwuKncSXmt7PlpbJ8SqD3T3THlSESsey53A6fBv3NVTlv6JJudGZ4VeK/t8BjSu5fmZaOGOGDHC/Gitb3JWDlx5tNWCZk5bF3Px2PZXXClblNHCOM1OCJPeMmfJy0nPVPZHLRfySe6dCb/ALE5fY5mh0tGrEDKZXpwVSF3MF/piMnXhNXu0GpGpcJbPel9jMU9PLyUtnPVL7GBrg3BKFT9+F4bLlkmNzg1R/8AZOJFX0Ku9/uVFVPS52H4dWNh0k78Y+koui08Liqw3cyOaoQ6aHrq7DdVb9PJCuTVyLuJNa33LWp7EbCWSpdBL5iB9mXuJzcicH/Aqn12JThFnw6EdegqsvDKn2wPZFVMFXKN1XLrlZKO/wBJRek5MGCqvoiF4dKZfxY9Dmrqf38mnw6XU+xPjV+qRp8KlUr+SatyrqVW2Eydh1NW3Ja9Cf7HiUvMkGofLLL5gVj7FSd5I3Q3uhVK3qeIvzJVopl2ZX0NX2FUvmRTWTFztwj6TgxHCpPe3l00Uup9jV/1FX/jSafDpVKOnBUIqPUhuw3UuUSeKkOmV2OZe6U+N1syKoxZnP7sXNLqjozw8KzyWcolE+INqmZKqMl/lKPE68tR3TE/zHieH1GmyNix68J+gL2PLxoo+/GEpNXiuF0RFCVKKlT6GqMZKqModLyV1vayKWvRlHhrCRX4f/6CJsaul0asrcbnmRUo2Pw/Eyt+w8roPwaqZ/L6FF+dO39Q4rVLWaSH1yVc8rrkVKb/AAvQem6gqU03K1nc9epSujJeJPuY2Gf5X8Xahl+UtWXpn0422Lr2CNuNb6WXCauWk5ab9TuzVG8F9x298pjsVeNQhrGRraRU5p2KPEfy59BN0zG5oTlJjpV6OhzP1LVTTiOhQ1XfCZFS5qUUVKZWDbqqu5+PS5q+ZCaiB+D/ALCHqXfUK7/c0bO5FMtu2TS4+7Kl9ySrYmeD+JhK4m71eSMVF1c05G6fYyW4VXvhEUqWaqr1cGKHkVJK+U0vP8Ca9BVbDtKqZFHUhshq1VJV4X7Crj1KGqua5TTVRdWqRoiejIphT/JR4tP/AHI/cp5SM9kx6VO8SNuhKrpSUumnmXQTS0+pEd5Ze1ifm/jg7/sZuVb8Ff4lJHfr5rGqnI+pPnXk/wASnUjlpS9OEWPxKlZY7isUwvdHGEQ/muV9nYW5V4fez6F/eTuU1JxUUyoY7cy3J3TwL1KK04qW5ccb3IezsavleR6VCgorMU099yJ+/UtirbhT85lk8LkbcMea3wFkTXZEaBVUu3fyydCxceke3sMceg9ieg21diT2GuxoI6FNSwWwypbZRVa+R1fMhQK8tcJW39zJAhPoNzkTkibbD4XPQ9PZZ+B6LhzM5VxptFS8mRbmpK3DszXSy+fYLhsJL9zVuNvoajUtkaqXeClkrdDuKKxXJkyQZ8mTJkyZMmTJkyZMmTJnyZM/Ay8+y6GrhfJp2ZQNEeeUJNmUJybFyEO47q/CJM+XJkyZMmfoly3sLksY+wugqk8irSvSKNi/ss8cmTP1Ox38ty1hzwVdI2StjTUNTaocD/QkMlcIp4tMQqXuaH9hmmvfBpexq2ZH6DwYPeJfCILmqnYR6CqFpwyjqXyjNvr8EkuyL2Rbjd7kLrw1EdWadyNmOoaFSynxKXjI2tyPr+p8MliE87kLBUyJwffi6W+FPi05RLxUONtj/LgdNSLfWk/KqeGrfYQkssVHBKMj9RvfUISXQprpyLuyyKvDH1EyZ5ahr67HCRFvlsfyS+kkzdncpH6mkjoyClfKaf2P8w5NNRV4bNLxt9bjjPFP8txf1XMD7wT0KdhPpwXWCPleCegofdDWKkaXlCq/c0sfVEfW0J+Wo+xVe7qKid3SU0vYa7cJnY708KVNjWiafuVUu5/VQOpZ+uxwtxR9imrqN9inpAvEbzUJpko+w5NdGCRPZkrDHUjWtyV9djyUlIvtwd8i5uxUhPg4zsOeEMVS/YurDoeGQ/r0i6rihEdxrgmV0txqRGeF2atjS2aHbuOhkbHdEfX44o+5UvudmR0PVHNcjrwjhKyjudGQ1+hk+EdTUhNYJ3O4mQXGW3NU3RH6EQ0ST0JR2fCf3IIfCN+D/Q0jXk/lcIJ4XO/6Knhbhf8A0t//xAAsEAEAAgICAgEDAwQDAQEAAAABABEhMUFREGFxIIGRQFChMGCxwdHw8eGA/9oACAEBAAE/If8A9VUy0e1KmYyCbg/shCgucNUVHIgPTOIZli/Ur8GLUbIj/YgXCVlEoLJTYzxU4Dp9weQNsy5W+RN6KxhgHXKY6wrcwBp1CrHwyhUZPHzEcf2EiojoEA/xKjFpX+UuJ153hOyWVOxVt/xMZ3DWWR5qE28etnc95nA4ZUFRV9+Jgb+4RzBix7Q3cPKpfRyeduf2CFtEQgl+A9sboC77IABXhDSMwm4j/N8SuKd9t36/+y1OjFZeal74iLpjZAFexI0rGxOV9wN16PSZ3RcHUJC3RtgSlhcZMQzFH+pT1PantT1Mp6/cCDpCtX+JrmHuWuAcm/l8Tq74vIzWHtCsxSr8trHtUd1Yw6wN5mCnYlf9+01qXC8M24MAKtF09GmmrgwdHJbmXg5W1Hssl+Yb7YIcM2/o6SNxN6M1DKFnGKlEO0RCMxHkPbBftakIaBUp3muzMvUBy2iz2L+JkFy58vUKxcnln/ietof+GCdAbSrJQwpNWjuYrPdZeOYcNnDD4uP08+kwq8yrhrzpiXgJXbiZvh2Tb6gXROJhwBYWRih3Ns0hPyh4lI9E4PwhjOrJsYr9nxxDJUEoJl9hBv7quPcTCxbgce0AW6WcP/qWGqt9CwzwAmK4rILtO0Fbbq4oZzDt9TVR/wCSS7jo5cEdVF9FmmASmFCy6Dd9ynBVTlOCP0AsyFYjGEQQMXXjMN1Mm2eZxGXcBrC9RyO51qFkzbg7g/IF3OpMUMwnInDRTJ+yIRHoK9xm0B3zMrYCrfiIxutXj1KYNvG4aQQ0pwIkdi7iHfDHHq5iSygT/k4jzYrQGFEhtVFrKlIB9rwlwUMhkOCa4z3e4egYImAwt4FeHJ9CmIbLM6EcEI3/ADiUt999y7D1PyvqaayMws44irLIcx877loHDFeOIKHGEkEHjAZuCcTFyjjYifsNRSURauiKwr8ojsC4dw4G8CugZSwFs4gFtv7g9cy41HI/gWZH8JxOYbNTDC/+uYlXSkLqk5gTEQp5ZaW4VaupxLDVmLmSgOFMpkWJTllZcvB4kZg3E4ibwgBqUwjdfi5b/vEXZyZhGj7JtXda3DhwyQFufmyhaXDfA3m5WEzh/iVt1qXYAheSaG5weGl+E+greycKQjBNZ+vUNBAHRfMOK7NXNojy0xiN7gu5sp/incybGya+dQUgGmjMFpmI3xzEhz4H81lSugv/AHMtlvIWuYqVC9qlg+wDmWZdEBlii8Sy8cOo6vat1EDcukEzOtKuIU58Jl94LjmmsS01TX8SlTgrD1DCtnPme09P8JaVhQ0zAyym0MiZsnqpSoYLRTYvtCWFbfiHaKbYMTGGCOktv0wliFGHgEkhO4nFEFuiNamwP1ahiUw+Bl9yJ9z4lAwnR1KNmCCxjQ20HCoW85ylPxK2KMBlfzDuBLZmpwBdHX/E1WGqc+gjRnQcB/ti6VXPydynXa4uj4l52nGTMIz1gaMbSiuHBBg0wS86YXkrEVHbFxlqL3KXBpHEsfu83MLDIl3pfcxTleVRCgXy5jRg1st1Ms6dkLekdzYIJymO2HmfcSnt3cVwsMxIaSxEXxzLUxLqp24h9QEA5nHTQEY0nCTZH6isUY7CuIYKp8BE2qEM0SKtWZbKB5kR1IyOUYxtgrU0Yq1V5lFEpzBRU5I8SlmhTDNjNYtiFMxtjuEww7hViakI1+g6hyfhmZR7dSi9g5O4Cc0/EsC+cjBrq4uVgKnQw16jsmjm5iEsPEKohSVwQBcjcaRjTBm7rqVwLWXUTMqZLSrkjFFg7W7l5SpSFzSLhhBJ4/v8JIJrwAq0Th5sj9IbBC9kr85NMJQrrl4OguNQdCte5SL9pqFYLMe1v8wwU69y96LixYt5Utt0xQF1Hm7qprOQ8C4oMLH0HqNNruJyESUfCTYfCuZSJQfyM1E0xwaj/HSDai2TKWgs8pFmT2Z5nQY8bzAwo5hwidCWDCW8pqjC0tmVdy8zpLgwz8FXl8bQbU4uFwmlm5hE/QUz3Ccp+I1ga9Oyara0ZXr2x0G+0SUWjcpLPasyvSrJeZmsu+4q/EFQ4i6jGKOfoKH0FCnfEbWvmOGxuNjOZr+CowhzFnLLdXE4cPcMF1iNP9PcDTBun+YDJzAQl7i8xtSpROfvKmBhnVHcwLyicGuo7DF/tExp+UtLqXNIU5+kQJoxA1OPmiJqJsYRP6tTi8zMUdMpGoOouxfUyYXtqFGnIhGz0uX4oYk8UqkdRrCLMqEaIni/SOL6UXM/zLxKsxipbJ3KdT3BxmDYv4i6cQ5JGbmbw1AtzucyuoFwZit4gaErwxtjNWF0zE4MKdp+8uXANMxUD2z/AAZLPIJKQkgtMHxMZPAtXLKNmf01J9x0nD+ZrN+9xzcNMLKKsb+EqTdZ9y5TITLv/syifiZzFDS6lKqoRnwL4WPgxirxjLl+BjnMf5im24XM1CH1CijMBNOI9mAtEZcoSl38wTRUt8GHCYR0/wBEU1Awn/FDlVOEx82eH5wq7h7yvcAzOHl4y9Q/oZMOkj9oi0D3MwL7JgI7NMFBwDD6lVvbMyli2Pcy3/yQtdQT4MemXjiLcESJGP0KPBcuXL8XLiImPWUcS/iW8xmTRmngYQfMJMy4H9b2vz4T8MA4J6iXrtHo85w4MyDeIpqzHTkitfXUPcqUp8wf9hNzJ0wVpp/JFds4TkRwQrBkIA1HVJ4DxcXjAOJwUq8H6B4iL8KyvirwMX4PDjxQfQjMiosYDLNRiq27/UJXRK6puY4DE+vXIBYPuesdxlQEHptdkwxxtKe1o8GRPVKvpM75cOJW+Zj5GEbZmwVOxRJyynUFL4l3mKlEq4mYQ8V+/wA6xFDeZu4adseXF/H6U+nFTxAYVU2+qh+Zjw5PtTkFPZLZbcJzO8SoepBXnoSplqEHOGoYcylKVMGLw+EK+MJqh6Jqre2VMQvol0thzPS/iVZb+IksULzCjFLxHUaXHUz1K2knpFkplcwgTT43jnCPbCwv30R4jYX9XvJyBmWjb9RAF5lRiODgnhHzMFp8ErtprwqYbEY5IaeIWO/HGMgiMcquPirfmRTp+WUYo9ErxuCu2kKjguXOARYdA9QzOf4jORF3zNI2mZjHWw7lZsm5aNk0vMMWjc7vEupyHoz+OBMAa/zGrZe/1RUDxaleIO9tTf8AViG6jsG/Udih9zmsQOgyYPJBn5ljOoJdcmocy1SquKRgWAjHHhDjs5mXxCvuOJrXURyg7VbMu9x5tvE5Y3ywQIvqWI4nuKckbvEZpQG1hYV8UuapjqZytky7in4jKbTO4DkrS0ocYIk+bVYjK/CUaivRkgsgdXDvXgMZr/T1A865qM5K+o2IWSyLG4xbikwaqbuDrtg8DySydVsYNYZigd3BEr1wvbcPhnvxb3PuKePzPxian3hpjf8AMWgxV11L3/RHuwB7hvD6xPVu1Mx7zqAsxwTMV+WbXKG7hkEhQoLdUMITN8NTaLFvdTKCmcEUTCXmehAynbyOO5Re+TqBkX0wGAoZnBlUPO5qUIZIFcw8JJggz+kIH1OEdyO/pNL3AEjZksRyZleDxqfFm/qVkcls/ixKDnDwcRby+QqhXQStEb737RQvbr+IN1HhUrU/GEmcRuDMbLbZZhwFE5lvRFcQn3xAbuyQW1EcTQdmcOZVYxQ+UQ/HFTJ0O/QTVQ26viDsPQ3G5W+WFMu1aEJxwiLcyqNvJUsIb1csdGbvqEsBhEos0yxcdjhLMnMqdpkDEhh/SHmvImhXEfBfrBU5ic1fBl12o693ZhmmtzZh6NT+TT6HqxYjuOBlOvllyKGwz90ojcVtWH+JRMIVEXDu46depo4waRx0ly9dS4sdCIDrZLBvGz1O5imowX/gQouKempcJSjJcr3B2gUCFRzQzEVMc3cbcDmk0XAP8zMdn+J/qD3OYzVvmN9iD2QsVmCxQfzMTuKhHiClU3OJRlYj48/0ZD6sMYxbX6q2UwtAjPyErGGUw3B9FQI48CdAmVP8sPh5EOa9khRa3OqATK0wCQkc0UlQUNrm6WgEfDMF9kKhixTMnTTHXcXTnh468Ahrm2kVzEMv+Z0wRorZ7RQN0OYzv4gbrH4lALkb4lrs+Tr7QOiyq+a5iie4JqdNZPeIWw4j3GMex1LuYVZHNwZnexWfmUgvGjBubILUMQvWJUWMM3+s/pkIfQHCAFTsmFl79VgauDSyeril0yyR1/GUeCGkJ4JXq4tzOCdY2xKGdPccHRxMBZQtPuaohrWpns8TuXFdBs+e4AcsMzWlL1FXNmLj0GXi/kh8rwCY4wK1xB4RDT12QC24UPKgLszaBCElrTFQb57p/wAzKJOTNeyJT0cHP3iOBycUaSOVasTldyeL2EAwyL6lOLSqVmszJdDP2RjeytnWZTKcvxM7Gq/aYY2GmYQ3xniFZqGfwx4cRvTx9Iu/Q6gmzf2meNfcIY35JkKHeUeoqaLgXCoOBgl1mXL9SWfzB0tE+R8RONxrERYOjxW/75mL3s2w5DivqI4gKCOKXwgJANMRb+QkiYode5XuYrPUOc1meSIvIH5kG4aE5UwYOB6RH/QBG7LCOGFcVLQ4SJTm1vygpuQ4mRWIl3BtxlV3iBhy1uBEEYFDpO5c0+Nwi+zdP/kuVDVmAqIZISleDMzAIs/zMgWPXG0jC75Gtwdq70lg2y8xNA+yK5ejAsVurJVpsyRKrdS2Zv4uPLHL9R/QqVKh68oQDvWY8RIaiqzw9MvsPaC7WWX+pNkKDdMRBit+k2CVFHERXfxE6w/ywC6VCJ7tEB3iNWL1UMsixcrMeOe2YTtVHzHbTorBbWy/zLG+J1OXorUfiJhfMOMWAhWSYC9QYs6tOXZGtUHbeI++49PqAzLqG8Rkyaz8kRdUrwaEsO2yrHwjQd7HKQZA5LY3ASnrszKRlcSfmWwGcp/EIZ2Vb+IqFinAICqUpnOJu9telxZE+FxMjj3ViJalNOp8BiD21bLWsCYuSI38zlHyiMy/j6z6iV4qbAlmFFvcdCCJ4kbxHmvO4J3WI/BG5bhepx3f1OYlHdmIV4Kie0wmsxcpgvUXwPcfDROItJCqGy2JUxKVMCxlmfmC0MDLuAwzmjCTaISS35iCJXBtACSPz6grU2o1bXMCWFYyIYscZUQLGf8A0zGHN2AwLAdGfzCy3E6lLnRYgig1vUHFNYcQrlqYheuFaXCrkdvsQsoaRu5julNtYiNgvBeopytlre5a6NepdG22pQT7y1Qe8+00iJu2Df0lqVK+o8EXpmJnw/LNsPkmzo4iuescwRDqHP21BemUioCzmBdz0y4B7H10Q3qVAam4WgzcT7RULaVieoNLiEq36sYug4uLVXfUDQR82GX987e47rAr4uIrTJkrfgAinaAixiqHHMemmvcVyEWLxLUvEodm3pEX9xLM1ic8S3zI4eomRlOpQHMZjHCckslo/CWHzUMWfmFqxQPhR1MgPsg3nHRjmO8QGUQFVBaD5iDcBBtTSM2D9FSoEqVE+hFiVawGrke4G0PUNoTxAqURzULq8g8hepbGW4RsIl26IgfjYUK3CQEBUWL9VDmbJQmTuXtFBMVQXVxEinmNwYZh3mI0TrE3uqLrqA4AcdwyxtqOkoujVu0uugCNzLTMKpipeb3JtRMZFjcaNkQEvEepMGkWNfAIKPGGTvCqqQ6kGKrC7I/M9CPUlLWC4ziM64jXgi0Kcy/J4CH0lHguJY4jNBcFBuKJjN58MYu4dTlibmYK6dEem6ckwE3UrTp/xD9xkS4WOSYQ4e5gbZjv6gW4jYnB2R7mCjxmD4RRgOI07Kd+4qMUvfELQVuoCvQczgJ44mO/HaiuZykRDEye9PY8L3T2S3ct3Ldy3ct3PdPZPZPZPZPdLdy2X/RIQ+M4SeJWKceFgR95SrVyjwX0t/jqXTxaJgHGYcPDLDsPU4FQh56o1EjRi5L/AKCLE0sFO4s347tJU2p7pb+zbS/xhB4STxssFtxgXED4lHA8vtAqxwZha5m44loWOSEEc3ki1NusrQ0ytbBCuHqDwpZP7uGCGfBWIjCKSopBfEXqYJsgCzE7YifywVq2Pk3KM3HZaDE5+7wWdHKFkRb15qZj9GZAzslqP3gOECBBiBmABRmWGoKg2fCYSjWXhiWWPRFNjBGzn2aHJ7VDO6bik2c4OIGNdTkr4ZpgGmAVY4GI+yJZP7vtNcEEwgrxQA3M82zQCGunbOARAJZqmBosH+2VvVSvie6FHgxAOL7QCM3RlFHMS3POGWg6Nsx+8jEbYwjeC3cffkjn931TWGSHdw1mXLtoPbnXcxkQDFr5WUhmdR04mwicCn8SuDV0SlstLhy7qK37QWV1idTGIeL4iiVwx9zmlOdoxVhztiN3ELKaOJfZ/eHQlxIajwnFTKWqGCYgFBgqfIFQFKcOVhTtuAKbQqohl3WamJfBMMmKEILsovvDMu3g/iDRZ5xLaeyB+QljNceogEqn5hAtZzNytT1HzIrb/ecDMvQ8DYDmalzM/YRFQ21OD15cx2+7hNvSaJk2RkjDmmwE2vebgA3raYyVlsiB5RF7i4JDbUAthN+krA6QOYF5g7FZhiROTmZxtGUZS9fvVUzBIGQjk2rqKgSqzAKwtLhYbWOpgIXbeoDTjNiDaGcL9zS9kqJ+XfEV2vLNRyNxFFtygq3pBEL3syKKnUXE+Q4nS/qLe9Tsy5I7X+9XCXSwucAm09EoK9VFRjqozK6qxMg0VPUVUGLor4mIYpfe5jHlb7luTVw7iNyljAMeiaxrOTOv4SIXYMQj1TNRUi8YSrjEgsKLfzD+YJap+9mGZJx4YpBtXMfczETjeyAS9Yte5egaO9R6dbfmVEac/eOYTQkX0RqIJs3cwdVUGbOIr2OuoAwVTEsMVQaFuSWcykxhzAvTe4rW/vmVaY0o5lVDB1NYLtq2DycxSERB19oCDbAlNKNYQcDX+YG6ys+pZdw7jRerPtBGj1Kc4SiG/sRmj56TVyZcychCbh1L+nH77RRZr8Av5mFavE+BupeNukd+VGDNK4YOHWM/MqKdyTYMqz9pVC4rJXECn3JihBY+8PrdnpjZysRW6aQpb5aeorbkmUOY5f365dmdSmpW479CHHxBmS9NkT21RKE9CdMdJPC4leORKyBzxHXwZU9GWcIzAbGmfmE4adLzMDV7l4dS8eP39rCUkupmnwzKj1DZY4mw/wC1BnQwsuOWmk2RFhlDsFPUC4xyitDeGAvlK6MO5QOoJkxB5uExsi/7BsVOKK4rl7hrpcRwU+ZqHOwyl1b2TZRyVFXo8y8P8JsUzWJOZeNtNblLGOEpXHuY4YrL/YVbKiOUd6l2nbcyfclVjr+SaVfOJV48a9TdoHB4hh/hCPRMM6MI2zAtTFyf7DGpRiWRV2dzOGtTSz/0j+Dv/mPfPJ37nv8A9E/7fU9CYbnK4j4ERZ/sVlAwL5jXxNf6mqzjh6i1/siN3Ac6nQznP7IGpyso3Gc1LeSd2BwxGpsH+zrZb/dH/9oADAMBAAIAAwAAABDzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzD4ocPzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzw35q1vKKfzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzza3860wVr7zzzzjDnDzzzzzzzzzzzzzzzzzzzzzzhhYdAZM4OZ3zwSUSAgWEkjTzzzzzzzzzzzzzzzzzxvp1bIA9gU7QGy4KseOcdP42kzzzzzzzzzzzzzzzzyHJiXur1SzWtv+zdY6ePuAuV8KmnDzzzzzzzzzzzwa34nxZlTr2I9acFiUMYBoSnWyieu/gnjzzzzzzzzzFUDhecj3oB5QQNli9YYJ6j8eDkkwjOeuqQnzzzzzhU1nFtyvNnhqtVs/zq4jKZJIFad94R1RGkr49Hzzyig/SuWCBdnlkgCe4/80cIwwSSdL/7GQ1P06LpuLzxKJ4O9xziB4xaSmbIWFr4Oh2Fdenf/JWB+dZH8MfzwPi/yjVVWJ3yxJ31V/i7MORW0KqhcSWJe62EJFUXzyDsF45h0MEQboj9DmGaw4YTpO1dQQ6buNgm/EjvLzzx52o1IYDRRjsOaTJHYmccv6lxcQnaTPEUpGpZEvzhEyNJ/T1ssYVQAVHSIz8Um9DE8/NiSdoNmMPmjuHwk1j1r30vCV8500Y+dktHDcEsVdxLGVmn22EQooBzxJBuofwL2RojUMXtOWLkU4FmKWaBk9BcaRyoPWvXzzw6wiCqSAJ14ywxxzyxyxzzzE9jh9xmbPGLADrCvzzzzzzzzzzzzzzzzzzzzzzzzzwN0dN/6mUxqg/55zzzzzzzzzzzzzzzzzzzzzzzzzzxLy1CubKopCecFnzzzzzzzzzzzzzzzzzzzzzzzzzzyN4R57YZYYyryxzzzzzzzzzzzzzzzzzzzzzzzzzzzwsr5+Kbeo96wpjzzzzzzzzzzzzzzzzzzzzzzzzzzzzwKV/IccN5LaXzzzzzzzzzzzzzzzzzzzzzzzzzzzzzySsqP7bf/oLHzzzzzzzzzzzzzzzzzzzzzzzzzzzzzwHufJOZSLvVzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzwJAsov/v6Hzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzxb/AB5Vwc88888888888888888888888888888888888scs8888888888//xAAjEQEBAQACAgICAwEBAAAAAAABABEhMRBBIFEwQFBhcWCR/9oACAEDAQE/EP8Am+9bpmEev4NQNbhzmY8XAracrFlMYBp/AkdZzDrwgHdjeLJMvZMIfgz9kocLuZ+7/JSc+CVI68qYLnOBfdPBFZ6yT3uu5n8H6n+lA9zwllttt9eDcngSwvRBF4I+ZGC53jc3mkrg/oridFn1bbLbkeFII2EjHPhzdW/MXfh0C96meFmfl34rn2ZjzPENuxvU1wXCSRcQ2y+D4H4EcEvT5cspLhZ+L/cTu3E44tdwuHEo3tC8zrCwXCRz8d8d+dDxQZFSzdgNVvl4CXdEXau5iu3z0B9S2AOrDEdrjeMbQjPhnMJMMN1f2WHdwXJLdg32S47gSLVg1tnHjl0wmbv+wpn/AJXu4bphPdj7tGE4SHKk8Hx302ADiCg5l8sOG3ZJuk2se5k/cRxK6bsmX7Yby/D7zPkRCnTA6Y+2w68ERycnJk89FnU5EZl34qOPhhNUHgy2uYbNTuAcbZx8YcXbBsYmTPgIPwK5bEvlZ4CXUGGeA23btwZyymHMFnGR1WWWZPhyOznmNwZBiQl5tnNukz4EfMmaJkD54z7jvLMMtSvcJds3GHNxRgMn7Q2znJPS662UnEzqeIz5ySThuWWLMwQWec8EHjLdpjzywjuybthKHLC+yc5eByPB3zB24AxI2zMmLY5zPjXY07fQnzdMzCD5ZBMAR4Wu87kGuRgXCLzOYcEauZzzdkyQ8QgyjpAMeri8+E8xlmfAunEgBYc2YRZZ46n6Wr7SLDO7XZ6PhcLQYh6C9MkqtYLI8z3zdW22+H28F8NlmKtWHN0y1+yy23H4knLTg8IsPCIAYfBBVZILf2j18uOp1tPVp6t/a39rb38ZD2v71/Yj7Vp7R1p3nEWEtJ9CCNRmkAaktxIRKS+z5W4cR+jmDOD5IV25t2PcwcB6g4H0X9FhZ+U7kCANzXxsJiSJhHiSTuDWDPEuKjy740G1/wBsRVtkHd34TeGC0ObNnViBz57PHCf3MEXLOpcAR5AdeSCJl6mb0/cwywcxcDv4eK9v7uC2hsO/hAKzO/vf7E9Pw8Z7f3+AemzmnnfiCL1O6/fHLlXfx+kePZfwOJRkfAAidU7tqrX+Cd46g/S5InfsPQluX8l//8QAJBEAAwABBAMBAAMBAQAAAAAAAAERIRAgMUEwUFFAYXGhYIH/2gAIAQIBAT8Q/wCahwwy0GESejSbcRGeCF2TIpCHCGjM+RBP0SBdeR0CnBcyUTT4HlCGfUP0Dg30CYv6F8JRS8CMWOTbCEIT83McIZWdCTbIOEM7EhKaIrJzsnghPxqq+WdonYv9CWNkJFVImy+KfgkDDaThEUYQhohRKWRFJh23RMv4IZ8lm+S+WPAhgzrCbiEYDsBu3kYvHVqJWVbZ4oM/okRyWgNeByQbZaJ6GUonvo1eRIZCCWlIII+lWkM73kUTH99CU1pk4E91KKKxbHtesRELBWJtHKqFrCRBlBjUX0JTal0Q6iC+WFcDwd+DoC5kNvpyC1e5+B8wWwSQxQii9YIJEngFlwMjkYBKECR4IYlRGhXyIo0ZMMcLBdHGi0fhRti1znw6ILI2hzwNtnFjMvBlmo9whI+CKltKwQeDmlR/0UQJlgrcg+CDQliLC8q97cLgSCWiZuIfJJsIgeDfw5Q3QZIok2wORjopDANtxobN2NQY1UJGWr2XR6pEiFrNHhUc1mVSiEdlY8IycHhif6M3/g2/qUXPIlpMN/gymliFhaqEFqyNusS5igJo9l0X2SP5EgeqVpEhCs65M7xYokQ3mDuHKqLSXAu0yOkTBQoLAgQlFpCDEeRN1lKUej0TPJDL1W1kkbFxQnoSsszMtGXkUXZHsl2T6H8Ih00y+Ar0P4g/kJ9DkBxWRsEkbGby9Y2RrRKiUSS41/oZ2by2couQPqQwN/Y2Bs5Dd2V9K/NKKNKNJlYTT4LrI6huuvRi/WudONjnKGMS29/s70Y/TPnRk9MxeJ/vXz1Lxkt9Tg5tvXpGqJ3YlNMv0c7RfpSlfs//xAAsEAEAAgICAgEDAwQDAQEAAAABABEhMUFRYXGBEJGhILHBMFDR8GDh8UCA/9oACAEBAAE/EP8A9U0wZqswQsHELA8+IlNyMHMzhmIZCa/4PemvEcMS8syDWjjU737YIJHtgVgO6qVICUdbiFhY7qAtb4gPHzDVcOI4gRpx/wAERAFrLcEeSPkVeSvzDrWAtBR8xGnccOHJ3HKgCyaEv/fvM4jw/fzCjTYIF3fF6+IDsQaCZJciznTnzBthOknPXuAKFp9LxFo7gYCNkpUMwKpP+BEztZfN98R/bbQtb5lAoCjXAzUtYxCCg4o3sE2RwI732oz2uqlKFYMg37Lu8bPMvKMixZHS9018XGxyrfnk+ar37jCy2DRTNuml+Y6y3jmbOLeoiVNrfwnmE2u4VtlsGc3l1CFAho4mRNf8BYgtdTz3YTNtBRWfiXGBQ7eTSnj7RBFbI4C+qdX6YUjY2Q10LoRsP8S9MEbGEzW3KNmHHMahgBdfBq6xeKSa/ErYpyAKDn56uUuWVBNYtc6bYVaAAMcndFR4GWtorRTlPMBmju3KrKv8Q3rAuLDDKLTgeDm4Q7FTdjEFeIKf6dLxB9KCaT4n/kRPf2ontEROP7ezE8IH6JkOGWg0wa0nXUIkVQtG8eXtqCpNDkAZs6awkIgddGyKKGqHDfCdzDy0oBtOwrv4lUIaqNIN1TkL5jEQC6AjobvkwUZdEaJVGb7wlj7lOEiNtFtPI1iEnI0KKyX3gmloMFd3nuuNRGnQmfx/3MVWkGReCEKUrUW36Fu/oAuAjAM34mSKQoAUVdwXUpZ3HMAV7PMUIilvBkmHKu0mgGLwZ1Du1y0ya8TUw9RE2f2ovrtjo7UWlH3hYrXFT0nXkjgb6aB8nXmCIA3e+l36u91UxERYilkV0Jb74iPG1drtY1Qqr11CvUjoFvNXC23d4NEcMoHQwWUU2JfGoH1AMqvDZmsswTOLRl0cGC3Wag9VgayjthL9QYWi+FvqCagEkAtlvrmY81aRQHXkglJbQFHow9QLVaYUUSKv1g7SL4lW4DKlKzh5LTnPMEkcAQr3B8LqC1aH8xcAcXqpasZGLitF58cxBw3iaCAssMi7nFMziTcaIPRLJaiPo+OaijCV/ZgtxKJr8TD8C1tJ/vUZsNwpd8RqiXHPLY8PMHYGpb6kurP9zC10w2De62jA+yM9irOHwieqQrZ5jWFTOGRaVVOOhzFLRgVkLkMp6wbqVVGsK3z6Hde+ozUo2KWML57ouFs4pbQiZtoHDUaeitbArMShVIlB/wBPMRIlchTh8RK0clxFQF8B3MMtysRHn9CFAsp7C4feE2jm6mDgyVt/7JQK0Jd40wXE2rO7tmRTdXpmLFfIC74hG5q+EXIOWyBDkXvUFQwGbOINYyq/czBsloajFZg93MFRuVaBTMZVcy2+wiDSQ8SvOf2QQrtgusASlTCimcgG0ZkcPYBWffxzMj+wl02r3nHiWUsGi3V2Gk8xST1trZG94un8QisypCRabM3WHrEUxEkwVcjMAXQaTEGooGA2IbZZlSvYXhe735l6VKgUW00OrmV4NlkKx2XB0Gwahw3fHMzyWszUrLXplWpbEoJniNNcH/URvmqdTCt5ZnA7jv6bhYFDzBRrTN1DENrTfE5LS6hgt1k54cQrVt8OWDkvpixQDIxVc4hUKvThqzcGkKFMu87T5iZIK2OR7my8DX5i2C1hRqAJWSiXMHpLQ1smPB9xA9RRHuPZnEY5i1Vzfwygbl2giSLFW2kUyJ/YUZvmG21Boz7qAZsbwXybxKV6o8JeTpgvFGVfTWq4WARfLgWte3+sC/VmgqtZp3TC+Riiq9ZColcOu5R5pKusOWrs7z8zECllkFbKa4q15jAPAlCwF41nnMXS8wQObayucFREnIhALtM/iA3OkYs2y2OLWMW84xqEjeOCYP8AM4DwOTqo6gs46iqlxDCaRRCh5lwvHUpDl9oNs4W8epUK3kNPb+I2C0JRUQMJe0cg4zBrousChXmDUwpnQfjnEoWtSDLTwPWK8RETA1Qr3nVU3CizsJtU5h1MOJrb2VECGlTistTFK3m5llRtqr1FdKA74hYB3DPaxLZiBlzC9HEcqZLueaLW4DtjhgYOm6NaL4qJqVjuSImz/wC1xeWoohFOkuAjdezq4vhyn8r3czLgrPKg34j1qrm7GV+b7+0qx6CgC45KyYuF3wKRHDbsumuoFASghxG7pxVXaMOduKAHGxT8/BLRGtNh2FYrpLfMdrBJAg1jg4qMCKLOgzSpvXMCooVeGjutN6fUMqIf5A+Y4mUijFPiWszZXeNjDRkVAUuMv8QStZsdxGzLUCBciU9IiK04gpZxmolOEpZx1BCSio0p/wBIUqA0tbprP41G3OocjAZzqEBgIWqFZo5hoqMIaEstut79TiBw0CC518Qq9hxVppxXnNRakBAuhOPcoxKtQa9MBYGj10xuurS6PUNKG2WCUE4NbIuDd9aZreAruJFBMWLOGPd5lk5EmQeYvReZUb3Mu42MzPVx1DKwBmA/xRNEMYUkI/TkRP8A6gssCR8kAvA/EpIL5HI8mF11ZMK5E6lmlupx8cY4uF93ABFxT0pEvhWErfhfC88EGSIyVG6crD437hSLTCHktMX9qOoaWWwKkYVNjyfaHNUiozEO1rf/AJLMF03vHN9l/NzLpwUgLxKvGKYJgGAA01Tr1BOaNOHF5w69RoV6LMRNWd8XLQ35Ypaxj4mIRAhjLnuWCCvcFc8zAiYkUHDDZOypidtM3j0zjFzDWOf2l5WWtAyc/MKnP62qat5xzFtAM60uFrj4gEVIEKB8guDbhF6CtN5xmFVTFm1jn9txqGdJ8aJZYVQlUwjSJltTmGZKXVkrQx4Ud9JCSmK7u69RHbI8sz5BinCQCk3HMrmlaF1L2bK9cwtxkaYtJ1FMHtz8y2swTma4vcozcfWCM2AzCFDMQWCjuEZpz4jZ/wDOZSrTKYIxpBlZI9VdoJ7jEG1a4de4S8CgBq11DOdskDOTOw4dQNjhllNKF2tc6YNgciF5Jk7mCanQgc48ftKOt5Fqd2d9eING/F12fD6u/mZ1qALwtWV5lb1tVVCK6O7a8R/AUbos+P5im1VhttzKFR7rwYhlEg8DB5rYxoRwrkgwxmO8N8QrBXs0PE5VtlWnqNYBFJYF46qahNmUVeX1xKJ2XTdU8G6lXJSBQl6QOyLCwsXh9XyRjhW7Dk8Zl9FYOGIg0aWO6mplBZfIws/FNy9h1FYTggoYNNH7xb9pjlWIUEDC5qBzUlUuIInQJu4KnDInJKKe0jJoOpYPYdRYt7JpRivBMeyiMm5TzFOYbB1VwimmZUWGkB5itWILYmMU58Snr/40I5anC7U08yqaiQhAi7GF7Ireh0Fn+3BbACigrwPUEMZQtWqTGAlG+bzaUnDX+1MGqdOumTxcTMysOD4ajtcCsjQde5pOyLcLpxFIqzYyPmPFU230wcLlk4SV1c9pxEF0vid794yw1KD6wE5h01E2WquYxWDkjqEwkMNuKjO5G9D/ANj0AFBVPPqZFh141liOQEp+wxRltgbznN+YlaCzu8khEVKU0b9wyQeGMzMEO39o8jU75gmRSU+GYxMCUf3gL5DfDE26PUqNi2RkupzTKWLWyCI0xibBfzAFapiBfaXWMQ3G4MpYLLAcp113D0M40fVxVuPe5YbnUEmRCCKTmKfEsqLXiNZJtBP/AIHPLwlMNDowAczVUFAyLTMq3AVL1pHp6jW2yn0krk49wJ6iGaUMlPwvqGVzIyMJ5YmACzDgqKZS7M/4mXZqRmitky4fJB6AM+4IU7bqOygWu5fmU4JdZiVH5g0kxkUNwqpYajyN6OIkNBMCOiw5OyYmgdPJHkShtAAl0C8XnmUgpd5Dh8RsEt2OKiS0HDTD18zEsUW1wyjm2jAaS7TebztjIV88pm9obDsgCuGKZcvjGIXomjhsY0hkPvBQAau37ShwuGYWL5tgypTqGbhkrEegKnlHkE8uIhjV1ZfiYDFa0lyAiHJM1U08xNWZfEKh7jjFo3dRCsyqswMU4gvOZQyEdWMwTAzLii4k1Y22Y8RykT+qy1gGI7YAXEkug37wkTjzCzR5qBPChQR4IECI0ODq4icNENHa/tFvRUCGuqIVWzApLx6AXAyjWjGL7JV0Q5dQimHMSZalZc3gjMIrYytJcEuDfuXByNL3MCfGdym64dyumKdcRqJV5WSjApiZkATFs/JLqWKUa0wM+g3yKiFPco4ZYhzrx3KRQXm+4ZEOl61GRuc00xxYy+YG8K9RShXRNWDz3OWXtyxlpABNArcDZYXMMERa2YL8z8sSfovMmp6ZgmnbuCpoPOIttvlAhpr3AarLNstSo3KxTMhmW7dTUGDovULbglK5lgWw5qWy5BxxH0crmON/0TcIY2jJCb0BdYEwlj4PugR3C4Q6ZYIEhb6BAnpqXlHdbuXWqqqwjj/qMhW1TWGmpSJOsooCdV2sAHsdsKLkOo2s+owoR2xgtuCCCH6LksKuDDKEXyRREjEBzzKPiFKtpOSZWLeWVgI1q8P3l5B5u4G1SSkophelZwumXYWwMi39paqqviBYeo7lf/igKs8ZhMBUYsB4IfSNeNTK4lgxqLaAta65YsWLLixfoxAUj4lfm13maQe4Ipydkt6w+ZQFZvmZELsggtUZlu2JS1foZQkAu6wslNPU9whoZiYqNx3Q/oCkOWU5q5hENGjkiYLwDnwy+hemz3CSELC7vv3BsCPTeXWeIotYACxDsI2WQut+0GofKo5bmFjU3FS4YEzC6BzZ9Iww5jNSwZmLcLwkEBLeGW5gDmC5gNMYYKFh8kcFFeYdYdE7aCarSMzCQzNAeIQXOQNxu6IrivvLGh+C+X7xY/rIQ+gpq4Bo4AAT7mKkXxN0kWughQvzNxeiQ8MO6a1dEZTZSgBYzCyQLKVOP1eboceRwIbF2N+PtA2k5Jhjun5f4IWvdSModQcTl2Vx9oVXAMd8ygmZpnC9BQxA6hbqDbEPOPoUdqwjJKg+ukcRUzDX0iQnMq2x4mL4Z2p2M8kbQLYalOZuOI95yYZxqVsgsE+8CoYTLKwj8QgkNvdvNdEQIqbV5Y/0CH9I3AgQjqV4PUYOo9QZlFJkZqEx3X6SKCzTxKwKtGOHL7BDbgyw/wAkcWbL+EEdKdg6aj17sNz5nJUTRWZnvY5lykySw1MOpkSFS1BDiEgi2Khp+qYkqVMXU439pRMnS6JgyZb2nzCCpiVZb4cR1E5qW9seAs7CUNjHNIO5Ypxp7iiyTH5IYY1FwO8RRUBtZPPR5ifMQ6HRGP6H6kCG/pz+k+lQQIECEPKytwesqHELEszmCkef1OwLwlzrVbS4Upc9oFrw1xw2bGP3SOUbGjl3thYUIQBxAbIGnMy9QKVoIiKxuWmWDKFAUSYoQ2Y+g/QkHoXlK+8DBNnc/wDUPC6edWbwPemDGFvOIiMlPNzPKo6ySjA64RsEUIISsi53UUNNY/OIaGlMOTZFvfHl1NlLTi9y2pJuO/CAZxGi+GZxpEZQEhdxUxaVifbf6Wp/Q16DmNfa0b+r9GMfqEr9Pz9T6B9TqBAjriMK3AOoArzZPyP1UgEMkwGQyTNXDkaY0aAdc/mGFrugNQ8GJd3ywU9RT7yPcr3g6Zjir4iNKmTtpmT9ZRWEDGMdW5iWsy0pziNgZXQbZni/HVng5i/LV6noiiukHRiJK5B0ZuUgRrg+8NAVqriokCBnHHnNVKs5JoziC/B/KU9EWqC2+Oe6zDGDS8t08WSxCoEpvELpEAFUNn3iVoUgVZz+bgvjcGy4zTb3Sr9wOE08Mthgnc2pMMUN26SVKKHRrxHGOHkgqTv390T94K54Ilf0j6H0PrUIEqG/oELfQCKgN4lsZCamhFCZ+x/SbI4Nq4xQoNOZeUPVJYmVcjmGWlHHK6hBqmutrL+YNOzEqoV+3qHkFJhjdNVH4DeWPT0c3LZkeYgDfmBND7y6l74YhtUpZdy5unxvvCtYcdH3c/iXkY3C/LmX0cGgC1CXnDZlb/1HJlXYZjqaqJdfEfK5wXq5WUtsGBjj9sw9mDYBirxn7ypIGGh1iIgjni7ebK7gZgYNUq6p81BiaSNpZrAdZh1QAUeIAAKHwefcsdBWm+ODxzAAu3dWNOH+Jiqpb4XZFdrCxXA2S/c8UG04iSkWltpA1LWCHWpmNRKfq/qIH6w+hAgWwmiVuVzCuamCmU0woiAT7zc+f0my8wiBOxmiA6slxWRsnZNNErfSZYt0fE4TNGa8zIaPkQS6HEsrBlIIhAPMxBHLQ7PMrMvS33me37wPS+8qmUp1HtYJQA7H987+CZBFtS/uYPLUW7gyWw0YV9x4AFlq/wD2c8F0d357lIVwcFB0X3e4J4gl95dkBGzjK0cnA1/MPaucDq6/EagirkVvtrEGrw0tFvfPWPEGh7LIjOM4xNeLQVR8GpZE3BayNNc5P/JRsumEG2RNVuqjdRfzGivhma1he1eILAviOSAu34nZmedse8wWYD4FIbx7CoiEFdX1DMVSoRnszC3sZcxmONsijknjgKxKofqx+hA+hK/WQg+gYg5nMouHHMtjWo4xtWmO0/prTmKljXdXAgP8lTNVvQJTERGwvd47hwHMOkvV/FRtFJKaYgsu0AIYo8BkHyzRxtwDqIrFXlhCD1nSlfggVR9Wv1HP3qA3tLz/AAMfe/mCFTLQALVV/iZGMTgPApMtrbrFV0xahScjVYgUGJYW9w6XY7jNX/rNiDquWt5TyRAqZbi28x/yqjsXG9VTNPlATRpfMFGLJFq7Jut7iq/xNxoLYa9ykpmnNjhTv1GfE7Foj3q8xvExsqjeumXEKTI0L3xECzzdgZL4Q9P5ZVXcOujN1xTh11GLo5wZFj6xGxYoqx1edVAxhgCFZsfmDNLkV38wAXfRruO0ylWouS0tZlUZ5e4MpwICkNmoDHKUMnilgyhYxjGP0IED61Kz9ScwgXBAYFwlIN46gtmKJyjc2kuP6an5l5MjY5IkpbO7J8xg/SMwMS35GsEE9wNlNcEcrpqMOQV2M39KZUPtnYryvB5Zix2bU9NHWLiOFRY9iyxqi+xGq8eIFs2FZw1MfCJDkrP5mZkBzpvV+IXxYC9rb/hKcWeMjWCGMmLNBbNO4iowUlXfMoxWRqwciQWdgPUjlmqqAFovP4Y3cYKFsjQHjefUNAjLYSVjPMSGOKwOvnuFbojUZzwP3jfORdiGCoS4AAFhRVeQjCmyIbAOc6qUIoOSY188EVRHSjR+HJ8ymC6hdBsU9zjSLOrSUcpFuuGvxUZUBrSDGItYF13NpY7wH+YFcW7HY9wyMch7JokcXGqU9IRHvcte9E3YNwFwsfq/QgQ+tfqP0BG+NRMXxKCzBl8w6lULuC9XM3+6Y/pEiGzcqDw7jETwJdyWvG5fyt4xTd/xDcIEISiuGL7ejywnQcAD/XBGflfCPWdvtjK6OR1/v7ytK0aPHExNVJXbnMMjLAclZ+0piqRVudVKSBwODDpmo3kINYv3GNvAH2GMnUH0QpKeLOtkN2SwyHl2qHmaIZF5fGvmEnSodqq2PXqWEWcJwKXvqAmwoaarg7NGIaAalbOW7/iXIwjaGsp5igZQpKJneJpAczl9Y7O5WPpw0OBj23Ls8oUWw9AzxmFsCcshheS6mNagBg8p0VcJVAUFpWu89la7lYkta2Sv2NyiVzdELuYEBQvBmmB5NljobLiVD0pvgQ6yHaaYTubKRMJzBwWkBvRiNCybiH6GCI/VjD6CH6K/RzBcEGIECtymKAlZUL+YRaGu65gMZGvibhdfqB1i8hODrlRSbAlpXHMN2EtM3gP5g/RqDEFrDmFpX43qZ4KUOXtef+og6poW7Vh95YUtRSs8JCz7oOVl/wAfEvc1NsqHGOYh25C8wor7XAFDQ8Gx8sxAbZyXZsiUoGl8zeD8QRADIOLNHz3Bbo95oKT4uCKPIDjYfaXhH2MFOROqlv7QsZGXr9mHqE1DWU5bxCIohqZHiv3h4EFczg6Rj3AyaKKfgGY25cYxOmxvm/M1Zccol44BtImtNSKE3db3DN/TaHTm+Hx/MW5kbFHoDAIWQHCAXTBTv4YO63xpC56xASBsLCkq/wAfmZhQAXbT7V9oxghQHYrDAWQXbjYiWDffTlmdeT2eLlFlsIbCCwUoiLvUdCyhqmUKUFFTUq7alIqFhP4jNxj9CH0PrUCVcqUw7TJ7gln9jgtm2scvxLw31VLZIQNvCk3eyW1vohx6o1Wbgmx5HIxq7MaYyXf6TLBFwuoXdgbIgdUIvWK8tTIwW00fvcNy2C2cmLwcTgQZW/khGEIorY6Or1ct4FaYCtnmOmdHC77zC+i5bMb+IesVTvDzAscW1iHZ6cS3Q6bKi097lgJiWrN2/mBgGkHJaL4ijgq7qxhfJEMhWm8u/iPzs0G3nl3uZJhcmNlemFSz4ikTL3mBip5TIoeGE5Vee1dPZMNOt6w65FyVGlSqF4UieIDEcMrtCc5pG5lWHgCaXmyOWhFUWayV1XcrWfIC65Fyx44h3haDlhFvRFEaSmCuxoxguMq0hhG3BRu8RROWDYpVgVQXAhuWR2mPtUAVCCisugrviPdji2ASrb3coIIosZVvPuMqMgAbdQY4NtUjdeSo9hgs34lgwOj1Mhpq7nMK45itoKJuzHiXPbGou363F+oPoE9QIECH0CGHNoCEzQHKB6IjHD1BqgiC+9EoKPP7PhlYIbEGRmwt6rIEG1ffZD3fDDq4KINcSxe39LGZtj6aDqUTa2UYQpScNQwg3sUfxuN1HWjyvEeEebH2TvzGW6OdRIlqMxosuvX8w1154PcdNQ0RpnKeg3LgAqHPTzL6Am1BWa9sZgViDpYjHouYcHazzAKVgunslydGB1RckxIHWimGDY5Crm9wOSVht8dx3EKUbDDRAYKAuASxVww4oMZIp89kZg6ABRxZ2JF6CiYfY1ncZDMBjwvM53UMqUhKigvMIQ4ASg8Zqucx/CNhBLdNYdlagWUBlNb1tJUeZdVSUqu5i6YLGacM7PEZ10sjVaC8Hjf2i28tKXsU24uV5S1O4uDb+BqFUUABUFozKrzsWGceW9QAabjQLvP8fiLdbVAjY1eLYEUQUF4Tf4iUwW2/jUALUp+ZUs02IEsu516llxNK3EitQ69I/RlSn6iEIEAguEV9BB2YCLkAFxl8HRKCUtdy0bMkceZdmGDgwJoMHmviCrqyvMaPF1uoCCF2U7iNnNH9JR3mDmzhq5bunCFpN8biAzgeL4lQx0QK+YVESwVL9R1a5rg+A+8wyQ6Xyb9sS0BfAYF164mvVg2ZKX7x7zYd50Khm6R8gbz7jNpJebN/iLXhKGawRIBLb6KZqq8yca+OYq5+ax2XuGLDBopNj7iFlaYK2fMREhCWNGP2ZiDHYxkapJQboqIo4pckSH9UA3jxHN15qZrCVCRWYtL/ABhgkiSKwWy8vZMQaIXkaa7rEsJg3UKS8m98wO1QBlisF6zzBF2kzhDZ6fE3IMlByOexv7zEcGzFYcLweIxXzACzXGUz3MHCBfduD/aiqlIWOb9ruN7dDrtqotwAASjcrYb2tzWLlygjeXGeJW4UFaqYNlNRsEcn8SpS77gOYA04lwQ/lajn6V4hlDxjWJAhCBBAzBAyF4C2GU9jH/RLCA1VqMLaWrLJZsYFBtcx0WyQiUgdQUsBg5fEVRuaoNEBmLx8cxA5dDhmBFqZKxivkl4dfqbDtmYckHeFLXhRH9I2Lp/ERs4pxjf8EoVgDQw5lqborBYaDz5lto7O6ay34iV2AtjBcDyqoFG+PiGCRXKiNmm+rl9IBAOGOblQoi74PiyGMC9mCNpCvUdIOKcp94MVKQdJAplwcAGb9xwhfa0JKkJbDTgICSjyaseIXElR6O/JFK1NAcAy6ssDSxEDEm3OGvXiK75Dhv8A8i6iLShNX7IIhVSN2JRiI3Ndm6PEIW0WHnDoOIa23ZtT3+PiVqqIYVzmGhVGtQHCHXHmJ8op09L/AJuVDe6cbqUTKOV3aVBbVtpXUC2U5eB/xAirvKEXkx3uc0FRFsRhZiSUjCKXA1RO19QVYahCCV6h4x+mrMISgCPDs5dvxKCQnK5phuDC/cChzogAuIoE40xKANINxFWmIckUrB7lvc4C5WWDswDQTM8BD95a1OEvtYmcvfAPJMjhyeIjyjZzMtWX+oCoJbrgAZhXCCity8wor71z9iX3HYWYcASkXHt0+4GFRcaKwQa10j9OwhtAuFXyPcycsBOMImVaKnh4gShEPemMvVRC7K4lTCFW6gzUYsbw7JWDCFy2RFYuZMZgBe89VEGpdwKo0c3EUxC4uUx2NXAALAdxOmrJKg0YWNeuqgxol7Y2wI37qcE2vMCAWKuAxi3E6e95ixhGsJQqZfMM2HWskOgz7bzCsN1UzsvqM8vvFUVXLi195uF94xlMU8y/rJdHivEV4hhqNzUpYJyyKsqF0p4IWHycQiABElDmBZ7TBqDIaYYDBSO5VYiEV6DaxdOHevHmG7GFN13LGrtA7xMD2iI6IvwYRSMxJPglagC64MQT0RXZf1OBSRel6YKrBaH8R6wGi0QS2hYgYVtXpHEbw+TTGz3Z4W8TR8Ahgb5Y+o2AANlMpS7V18xelqF0k+ZoMIVT9IlSrnFt/SBba+8X2/vPMnlTyp5U86B8oU1f7zy/vDtzy55f3nkR7U80t3Lf6LOXw3iCNQPoimpeZIVDHBF2qPDcLAB4mBLNTzSrkg1NPEFkuDLdWywGjhYGCLsuEKpWzseoj5EtfxCAAVNdMZwpXkhH+UY0bI6Foc7IgFgf6FkaJKy9DzA0vqtykDMVuF0rGs6gVJP5BRTbfmLcst7mf7GYY7EqC6gVKmX6ipqcBOz6C4J2kyeicRI/jmYZaV9UPOZ0MrFYenf3mS7yN5ht2icckyKJxGvMqMEHYMs0tWPBH0VOl8MzyKh01qAzC7amFhI48xU3b/dswSkw0Q2lGswATmXjWPoFGZVxc6SCMRQsUZFFi+SD7ClTaAOWaqzD3fE5Vdu7lrsUuuCBT69HJ3DzBBbl4iGKVB1UYiqr0XqcXka+SVVl/UtjVisu6FY5SOmG1wuotv8AdtXuWer6SXiYUFIO5R5VZYDBauY7rb4hVo+oW2j4gdivcdBfCEU0XWMzax0/7xIrqXcVcZvXNsQ3UMFe/wDEd0gPa4w8cocnUrSxYZ4bjRkAaFq4otDETmPMzC3sSWLwdvHDCp1fUk68BnTEbbBr+765l6ItXA43EkBG+JWG7WLJmPTllhFljI8eJqtl+ajQNE5ra+MbfEqhrZesst5S51+fiWj1E/MMLGxTRVnwQEFVPOLAVW24mbF+fcMitj03LgVqeQ5i1rQHmAmAUHiomcip2Swk+kzMVDL+ZgqBB1cDbxMcxKV/u+t2w0TqYgEIFtwSpYb4hnmwjMgALtgWAhw4AhYW4brrogLSRbLt6PUoEUctc0X+XzAKOmVQcDyYhm40AWhz5dxKqqF+gsu/2lNeYtrNYvzVHxBoICyd8y7xXbxeYGd8B0m4jrkAHaXuImSixp/0gbKF1zXMcAB2uA1qNJUBXuoqEFfJ6YQzKB5JfVXluGI/Iv8AvFw8zZiyFXtgac1l0ekFqZtIOXxzLQwzwoiXusHl5a8S3gLFxV2tdBAXGunJdgfK3LbSAOKxb8p8BBSssVkA2B9sS5SLs5fP7wYeYiGLNxBbU3bRHpAan4hLYN13wSBQFVlhOSOERR+BGUiNnEJSLWzy4qIyei8eUFhgpAgN17HXqCqFVycxHXP94MM2zJDlgWwcXV9TIxZlqIU3Uta3wQgoaniJtoABoPbAwVbJzV6+UYxzyiyPAHGyMVDCeDdeCOaUDfutdYiVWm321f7wR2TOF3VsJLJsOCjPzE1XM6pqEtcivMEfBQ81mB2rWd+EQUlk6vqBxYzwYXKydwwb1qC6tLnN3mdMWtrP96ypwyje1xCHeGSICsHI7iRQtteWXQtGYwHRw4xn44I56iEW2PPm5fGXNoXjHfEyNI8Aq98ZlYWsDTtf2hIACi1Yb+8MlKEuxNV+zK6qlx/MxLgB3ak3mxDT2S2uBk2nmVJEOw6h2DWXzXEpLsiOGMEMqt1bpmUW1+yW2BT8ktFZcC6iq21/vTWtZjv66uOi99wtqvbC9CJLabLLOFKPzNoLlrCm4q7I+Ck/eoCEr0BTHId5PEdEquchh+YTNRJ4Egr8ynMO2bLFWfeIJqyrwx+8MXXBuJpUKn3VQVD+W8xAg1VrZBEF23RDxZCvTuCDJ8j2RAmAOxrEuiIp5BGs2sP7S8tC5P726Eh7REoSG4C/R5YmxLaJUAeLzUzkJCWkDDFI35CiS/eYGiJacxWH4GWWoGPGBnnma4NpcUA/evcFq4jb5pv748wLlRccNGiOuravN7uYCxhs7cy87AN7IVA1LwtKs4WiIVKksS6Wi8F8ShtVPCRlryzFwzQQoHLHXYv98pWpIpRwsuYLTLKUGGWLVSZ+YwyUC71j/uIrgqPxmvxARA3paol0haPIkt5K3ii2ieyxjdLlVXVrGIHQ0AWr/EqaCtg0kLJlwaBxHgKQQYp6grFPXhxqEBTeTpqaGqJG3cwHfdqHFgReorQgu/EQSN7/AL6pTVMIW35CAhbgxEbc4ITNQoxlBpg2vImH4gWsXDYYbr/EZoFaOLa/37RMKE+zJ+YQpYEeTV/mUIoI5FnniMbs0BfL+JXhQV28JngCogjVOcjofzMdQoHYcSgTJVwzHNQXwncvRVUmbQym8Z8SlArIzGorv++8zXIdR0Y4d1Em2GqlANijTfJEDbN/O+ooFdhcY5+0QhSiDw87mQD5IjZ/iMgVcjQI/eo8KGzA9fOpcq0teXkiDSLN+exj5BFBuFBdr9nhgUYaDkhLFgJ2g5DL0vBgXZZA7PJFtKdHsj3l2x/fyXFAZeSVS1z4lAq6HHEstC2p7rIy182DMsp0PziJugloc0tP8fJKtIqmnqY+zuRTj94ofZSufT7uMYBbfIlbmijyJHJYPoeI2wN/8JNgqqt+8Wxod45ICrMOeGaEh7zuPTi03xFtv+/sW44ZfVsM0N2VEYslPvhJd4F2VIcfmMS4Itb2/eAKNMRycj8xrOUH0ZuUDSmnkdfEzmyrwf8AES4tOBw6ZQ5sv8cMY016c9MG0mByHxFZw21wwNYsaeYVWVxUYrf/AAEUbI4Z1DReZQjyXmASxSvbj8yyAo4+nDDQFME7NPs1GgGQhOr6fZ/Mqhje7bRwwAhi7EcXMRcOFdkJ1FtPHiUBGp6e4hDd3BU8BgAY0U5iJV9/8DZWR0Jh43OyUGg5XplraeJz2fzFyFM+yMFVJhX8exFTTJK6nSJoha1x/kmEEULxyXmPOImQ/cgThbw9nT5gaZ8F4gKziXxL/wAFEI6moTBNlPEE2Puv3m9uf2X/AB+0cqD+CdP8TQWo1zLpgizV+l7Ie6G+9J58+YFnwPJNpd+zH21XUVf+DohGMFWDuYVU9SnG7yShirq4AcUe+YLkrUt7VcYyMu9/8Mtnmi3MV/5P/9k=" /></p>"""
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)

        txt = Text.objects.all()[0]
        self.assertTrue('id="plugin_obj_%s"' % (txt.pk + 1) in txt.body)


    def test_add_text_plugin_empty_tag(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + "%s/" % CMSPlugin.objects.all()[0].pk
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body": '<div class="someclass"></div><p>foo</p>'
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals('<div class="someclass"></div><p>foo</p>', txt.body)

    def test_add_text_plugin_html_sanitizer(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + "%s/" % CMSPlugin.objects.all()[0].pk
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            "body": '<script>var bar="hacked"</script>'
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        txt = Text.objects.all()[0]
        self.assertEquals('&lt;script&gt;var bar="hacked"&lt;/script&gt;', txt.body)

    def test_copy_plugins(self):
        """
        Test that copying plugins works as expected.
        """
        # create some objects
        page_en = create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        page_de = create_page("CopyPluginTestPage (DE)", "nav_playground.html", "de")
        ph_en = page_en.placeholders.get(slot="body")
        ph_de = page_de.placeholders.get(slot="body")

        # add the text plugin
        text_plugin_en = add_plugin(ph_en, "TextPlugin", "en", body="Hello World")
        self.assertEquals(text_plugin_en.pk, CMSPlugin.objects.all()[0].pk)

        # add a *nested* link plugin
        link_plugin_en = add_plugin(ph_en, "LinkPlugin", "en", target=text_plugin_en,
                                    name="A Link", url="https://www.django-cms.org")

        # the call above to add a child makes a plugin reload required here.
        text_plugin_en = self.reload(text_plugin_en)

        # check the relations
        self.assertEquals(text_plugin_en.get_children().count(), 1)
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
        self.assertEquals(text_plugin_en.get_children().count(), 1)
        self.assertEqual(link_plugin_en.parent.pk, text_plugin_en.pk)

        self.assertEqual(link_plugin_de.name, link_plugin_en.name)
        self.assertEqual(link_plugin_de.url, link_plugin_en.url)

        self.assertEqual(text_plugin_de.body, text_plugin_en.body)

        # test subplugin copy
        copy_plugins_to([link_plugin_en], ph_de, 'de')

    def test_deep_copy_plugins(self):
        page_en = create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        page_de = create_page("CopyPluginTestPage (DE)", "nav_playground.html", "de")
        ph_en = page_en.placeholders.get(slot="body")
        ph_de = page_de.placeholders.get(slot="body")

        # add the text plugin
        mcol1 = add_plugin(ph_en, "MultiColumnPlugin", "en", position="first-child")
        mcol2 = add_plugin(ph_en, "MultiColumnPlugin", "en", position="first-child")
        mcol1 = self.reload(mcol1)
        col1 = add_plugin(ph_en, "ColumnPlugin", "en", position="first-child", target=mcol1)
        mcol1 = self.reload(mcol1)
        col2 = add_plugin(ph_en, "ColumnPlugin", "en", position="first-child", target=mcol1)

        mcol2 = self.reload(mcol2)
        col3 = add_plugin(ph_en, "ColumnPlugin", "en", position="first-child", target=mcol2)
        mcol2 = self.reload(mcol2)
        col4 = add_plugin(ph_en, "ColumnPlugin", "en", position="first-child", target=mcol2)
        mcol1 = add_plugin(ph_de, "MultiColumnPlugin", "de", position="first-child")
        # add a *nested* link plugin
        mcol1 = self.reload(mcol1)
        mcol2 = self.reload(mcol2)
        col3 = self.reload(col3)
        col2 = self.reload(col2)
        col1 = self.reload(col1)
        link_plugin_en = add_plugin(ph_en, "LinkPlugin", "en", target=col2,
                                    name="A Link", url="https://www.django-cms.org")
        mcol1 = self.reload(mcol1)
        mcol2 = self.reload(mcol2)
        col3 = self.reload(col3)
        col2 = self.reload(col2)
        col1 = self.reload(col1)
        copy_plugins_to([col2, link_plugin_en], ph_de, 'de', mcol1.pk)
        mcol1 = self.reload(mcol1)
        mcol2 = self.reload(mcol2)
        col3 = self.reload(col3)
        col2 = self.reload(col2)
        col1 = self.reload(col1)
        link_plugin_en = self.reload(link_plugin_en)
        mcol1 = self.reload(mcol1)
        self.assertEquals(mcol1.get_descendants().count(), 2)

    def test_plugin_validation(self):
        self.assertRaises(ImproperlyConfigured, plugin_pool.register_plugin, NonExisitngRenderTemplate)
        self.assertRaises(ImproperlyConfigured, plugin_pool.register_plugin, NoRender)
        self.assertRaises(ImproperlyConfigured, plugin_pool.register_plugin, NoRenderButChildren)
        plugin_pool.register_plugin(DynTemplate)


    def test_remove_plugin_before_published(self):
        """
        When removing a draft plugin we would expect the public copy of the plugin to also be removed
        """
        # add a page
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.get_response_pk(response), CMSPlugin.objects.all()[0].pk)
        # there should be only 1 plugin
        self.assertEquals(CMSPlugin.objects.all().count(), 1)

        # delete the plugin
        plugin_data = {
            'plugin_id': self.get_response_pk(response)
        }
        remove_url = URL_CMS_PLUGIN_REMOVE + "%s/" % self.get_response_pk(response)
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 302)
        # there should be no plugins
        self.assertEquals(0, CMSPlugin.objects.all().count())

    def test_remove_plugin_after_published(self):
        # add a page
        home = api.create_page("home", "nav_playground.html", "en")
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
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
        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.get_response_pk(response), CMSPlugin.objects.all()[0].pk)

        # there should be only 1 plugin
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        self.assertEquals(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=True).count(), 1)

        # publish page
        response = self.client.post(URL_CMS_PAGE + "%d/en/publish/" % page.pk, {1: 1})
        self.assertEqual(response.status_code, 302)
        self.assertEquals(Page.objects.count(), 3)

        # there should now be two plugins - 1 draft, 1 public
        self.assertEquals(CMSPlugin.objects.all().count(), 2)

        # delete the plugin
        plugin_data = {
            'plugin_id': plugin_id
        }
        remove_url = URL_CMS_PLUGIN_REMOVE + "%s/" % plugin_id
        response = self.client.post(remove_url, plugin_data)
        self.assertEquals(response.status_code, 302)

        # there should be no plugins
        self.assertEquals(CMSPlugin.objects.all().count(), 1)
        self.assertEquals(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=False).count(), 1)

    def test_remove_plugin_not_associated_to_page(self):
        """
        Test case for PlaceholderField
        """
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]

        # add a plugin
        plugin_data = {
            'plugin_type': "TextPlugin",
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot="body").pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.get_response_pk(response), CMSPlugin.objects.all()[0].pk)

        # there should be only 1 plugin
        self.assertEquals(CMSPlugin.objects.all().count(), 1)

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
        inheritfrompage = create_page('page to inherit from',
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
        plugin.insert_at(None, position='last-child', save=True)
        inheritfrompage.publish('en')

        page = create_page('inherit from page',
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
        inherit_plugin.insert_at(None, position='last-child', save=True)
        page.publish('en')

        self.client.logout()
        response = self.client.get(page.get_absolute_url())
        self.assertTrue(
            'https://maps-api-ssl.google.com/maps/api/js?v=3&sensor=true' in response.content.decode('utf8'),
            response.content)

    def test_inherit_plugin_with_empty_plugin(self):
        inheritfrompage = create_page('page to inherit from',
                                      'nav_playground.html',
                                      'en', published=True)

        body = inheritfrompage.placeholders.get(slot="body")
        empty_plugin = CMSPlugin(
            plugin_type='TextPlugin', # create an empty plugin
            placeholder=body,
            position=1,
            language='en',
        )
        empty_plugin.insert_at(None, position='last-child', save=True)
        other_page = create_page('other page', 'nav_playground.html', 'en', published=True)
        inherited_body = other_page.placeholders.get(slot="body")

        add_plugin(inherited_body, InheritPagePlaceholderPlugin, 'en', position='last-child',
                   from_page=inheritfrompage, from_language='en')

        add_plugin(inherited_body, "TextPlugin", "en", body="foobar")
        # this should not fail, even if there in an empty plugin
        rendered = inherited_body.render(context=self.get_context(other_page.get_absolute_url(), page=other_page), width=200)
        self.assertIn("foobar", rendered)

    def test_render_textplugin(self):
        # Setup
        page = create_page("render test", "nav_playground.html", "en")
        ph = page.placeholders.get(slot="body")
        text_plugin = add_plugin(ph, "TextPlugin", "en", body="Hello World")
        link_plugins = []
        for i in range(0, 10):
            link_plugins.append(add_plugin(ph, "LinkPlugin", "en",
                                           target=text_plugin,
                                           name="A Link %d" % i,
                                           url="http://django-cms.org"))
            text_plugin.text.body += '<img src="/static/cms/img/icons/plugins/link.png" alt="Link - %s" id="plugin_obj_%d" title="Link - %s" />' % (
                link_plugins[-1].name,
                link_plugins[-1].pk,
                link_plugins[-1].name,
            )
        text_plugin.save()
        txt = text_plugin.text
        ph = Placeholder.objects.get(pk=ph.pk)
        txt.body = '\n'.join(['<img id="plugin_obj_%d" src=""/>' % l.cmsplugin_ptr_id for l in link_plugins])
        txt.save()
        text_plugin = self.reload(text_plugin)

        with self.assertNumQueries(2):
            rendered = text_plugin.render_plugin(placeholder=ph)
        for i in range(0, 10):
            self.assertTrue('A Link %d' % i in rendered)

    def test_copy_textplugin(self):
        """
        Test that copying of textplugins replaces references to copied plugins
        """
        page = create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')

        plugin_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=0,
            language=self.FIRST_LANG)
        plugin_base.insert_at(None, position='last-child', save=False)

        plugin = Text(body='')
        plugin_base.set_base_attr(plugin)
        plugin.save()

        plugin_ref_1_base = CMSPlugin(
            plugin_type='EmptyPlugin',
            placeholder=placeholder,
            position=0,
            language=self.FIRST_LANG)
        plugin_ref_1_base.insert_at(plugin_base, position='last-child', save=False)
        plugin_ref_1_base.save()

        plugin_ref_2_base = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG)
        plugin_ref_2_base.insert_at(plugin_base, position='last-child', save=False)

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

        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
        self.assertEquals(CMSPlugin.objects.count(), 3)
        self.assertEquals(Page.objects.all().count(), 1)

        copy_data = {
            'source_placeholder_id': placeholder.pk,
            'target_placeholder_id': placeholder.pk,
            'target_language': self.SECOND_LANG,
            'source_language': self.FIRST_LANG,
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(response.content.decode('utf8').count('"position":'), 3)
        # assert copy success
        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 3)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 3)
        self.assertEquals(CMSPlugin.objects.count(), 6)
        plugins = list(CMSPlugin.objects.all())
        new_plugin = plugins[3].get_plugin_instance()[0]
        idlist = sorted(plugin_tags_to_id_list(new_plugin.body))
        expected = sorted([plugins[4].pk, plugins[5].pk])
        self.assertEquals(idlist, expected)

    def test_search_pages(self):
        """
        Test search for pages
        """
        page = create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')
        text = Text(body="hello", language="en", placeholder=placeholder, plugin_type="TextPlugin", position=1)
        text.save()
        page.publish('en')
        self.assertEqual(Page.objects.search("hi").count(), 0)
        self.assertEqual(Page.objects.search("hello").count(), 1)

    def test_empty_plugin_is_not_ignored(self):
        page = create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')

        plugin = CMSPlugin(
            plugin_type='TextPlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG)
        plugin.insert_at(None, position='last-child', save=True)

        # this should not raise any errors, but just ignore the empty plugin
        out = placeholder.render(self.get_context(), width=300)
        self.assertFalse(len(out))
        self.assertTrue(len(placeholder._plugins_cache))

    def test_editing_plugin_changes_page_modification_time_in_sitemap(self):
        now = timezone.now()
        one_day_ago = now - datetime.timedelta(days=1)
        page = create_page("page", "nav_playground.html", "en", published=True)
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
        page = create_page("page", "nav_playground.html", "en", published=True)
        plugin_data = {
            'plugin_type': 'DumbFixturePlugin',
            'plugin_language': settings.LANGUAGES[0][0],
            'placeholder_id': page.placeholders.get(slot='body').pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)

        plugin_data['plugin_parent'] = self.get_response_pk(response)
        response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
        self.assertEquals(response.status_code, 200)

        post = {
            'plugin_id': self.get_response_pk(response),
            'placeholder_id': page.placeholders.get(slot='right-column').pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_MOVE, post)
        self.assertEquals(response.status_code, 200)

        from cms.utils.plugins import build_plugin_tree

        build_plugin_tree(page.placeholders.get(slot='right-column').get_plugins_list())
        plugin_pool.unregister_plugin(DumbFixturePlugin)

    def test_get_plugins_for_page(self):
        page_en = create_page("PluginOrderPage", "col_two.html", "en",
                              slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = add_plugin(ph_en, "TextPlugin", "en", body="I'm inside an existing placeholder.")
        # This placeholder is not in the template.
        ph_en_not_used = page_en.placeholders.create(slot="not_used")
        text_plugin_2 = add_plugin(ph_en_not_used, "TextPlugin", "en", body="I'm inside a non-existent placeholder.")
        page_plugins = get_plugins_for_page(None, page_en, page_en.get_title_obj_attribute('language'))
        db_text_plugin_1 = page_plugins.get(pk=text_plugin_1.pk)
        self.assertRaises(CMSPlugin.DoesNotExist, page_plugins.get, pk=text_plugin_2.pk)
        self.assertEquals(db_text_plugin_1.pk, text_plugin_1.pk)

    def test_is_last_in_placeholder(self):
        """
        Tests that children plugins don't affect the is_last_in_placeholder plugin method.
        """
        page_en = create_page("PluginOrderPage", "col_two.html", "en",
                              slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        text_plugin_2 = add_plugin(ph_en, "TextPlugin", "en", body="I'm the second")
        inner_text_plugin_1 = add_plugin(ph_en, "TextPlugin", "en", body="I'm the first child of text_plugin_1")
        text_plugin_1.cmsplugin_set.add(inner_text_plugin_1)
        self.assertEquals(text_plugin_2.is_last_in_placeholder(), True)

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
        page = create_page("page", "nav_playground.html", "en", published=True)
        source_placeholder = page.placeholders.get(slot='body')
        target_placeholder = page.placeholders.get(slot='right-column')
        reload_expected = {'reload': True}
        no_reload_expected = {'reload': False}
        plugin_1 = add_plugin(source_placeholder, ReloadDrivenPlugin, settings.LANGUAGES[0][0])
        plugin_2 = add_plugin(source_placeholder, NonReloadDrivenPlugin, settings.LANGUAGES[0][0])

        # Test Plugin reload == True on Move
        post = {
            'plugin_id': plugin_1.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_MOVE, post)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content.decode('utf8')), reload_expected)

        # Test Plugin reload == False on Move
        post = {
            'plugin_id': plugin_2.pk,
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }
        response = self.client.post(URL_CMS_PLUGIN_MOVE, post)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content.decode('utf8')), no_reload_expected)

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
        page = create_page("page", "nav_playground.html", "en", published=True)
        source_placeholder = page.placeholders.get(slot='body')
        target_placeholder = page.placeholders.get(slot='right-column')
        plugin_1 = add_plugin(source_placeholder, ReloadDrivenPlugin, settings.LANGUAGES[0][0])
        plugin_2 = add_plugin(source_placeholder, NonReloadDrivenPlugin, settings.LANGUAGES[0][0])

        # Test Plugin reload == True on Copy
        copy_data = {
            'source_placeholder_id': source_placeholder.pk,
            'target_placeholder_id': target_placeholder.pk,
            'target_language': settings.LANGUAGES[0][0],
            'source_language': settings.LANGUAGES[0][0],
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        json_response = json.loads(response.content.decode('utf8'))
        self.assertEquals(json_response['reload'], True)

        # Test Plugin reload == False on Copy
        copy_data = {
            'source_placeholder_id': source_placeholder.pk,
            'source_plugin_id': plugin_2.pk,
            'target_placeholder_id': target_placeholder.pk,
            'target_language': settings.LANGUAGES[0][0],
            'source_language': settings.LANGUAGES[0][0],
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        json_response = json.loads(response.content.decode('utf8'))
        self.assertEquals(json_response['reload'], False)

        plugin_pool.unregister_plugin(ReloadDrivenPlugin)
        plugin_pool.unregister_plugin(NonReloadDrivenPlugin)

    def test_custom_plugin_urls(self):
        plugin_url = urlresolvers.reverse('admin:dumbfixtureplugin')

        response = self.client.get(plugin_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, b"It works")

    def test_plugin_require_parent(self):
        """
        Assert that a plugin marked as 'require_parent' is not listed
        in the plugin pool when a placeholder is specified
        """
        ParentRequiredPlugin = type('ParentRequiredPlugin', (CMSPluginBase,),
                                    dict(require_parent=True, render_plugin=False))
        plugin_pool.register_plugin(ParentRequiredPlugin)
        page = create_page("page", "nav_playground.html", "en", published=True)
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

        page = create_page("page", "nav_playground.html", "en", published=True)
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
        page = create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ChildClassesPlugin = type('ChildClassesPlugin', (CMSPluginBase,),
                                    dict(child_classes=['TextPlugin'], render_template='allow_children_plugin.html'))
        plugin_pool.register_plugin(ChildClassesPlugin)
        plugin = add_plugin(placeholder, ChildClassesPlugin, settings.LANGUAGES[0][0])
        plugin = plugin.get_plugin_class_instance()
        ## assert baseline
        self.assertEquals(['TextPlugin'], plugin.get_child_classes(placeholder.slot, page))

        CMS_PLACEHOLDER_CONF = {
            'body': {
                'child_classes': {
                    'ChildClassesPlugin': ['LinkPlugin', 'PicturePlugin'],
                }
            }
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=CMS_PLACEHOLDER_CONF):
            self.assertEquals(['LinkPlugin', 'PicturePlugin'],
                                plugin.get_child_classes(placeholder.slot, page))
        plugin_pool.unregister_plugin(ChildClassesPlugin)

    def test_plugin_parent_classes_from_settings(self):
        page = create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ParentClassesPlugin = type('ParentClassesPlugin', (CMSPluginBase,),
                                    dict(parent_classes=['TextPlugin'], render_plugin=False))
        plugin_pool.register_plugin(ParentClassesPlugin)
        plugin = add_plugin(placeholder, ParentClassesPlugin, settings.LANGUAGES[0][0])
        plugin = plugin.get_plugin_class_instance()
        ## assert baseline
        self.assertEquals(['TextPlugin'], plugin.get_parent_classes(placeholder.slot, page))

        CMS_PLACEHOLDER_CONF = {
            'body': {
                'parent_classes': {
                    'ParentClassesPlugin': ['TestPlugin'],
                }
            }
        }
        with SettingsOverride(CMS_PLACEHOLDER_CONF=CMS_PLACEHOLDER_CONF):
            self.assertEquals(['TestPlugin'],
                                plugin.get_parent_classes(placeholder.slot, page))
        plugin_pool.unregister_plugin(ParentClassesPlugin)

    def test_plugin_translatable_content_getter_setter(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.all()[0]
        created_plugin_id = self._create_text_plugin_on_page(page)

        # now edit the plugin
        plugin = self._edit_text_plugin(created_plugin_id, "Hello World")
        self.assertEquals("Hello World", plugin.body)

        # see if the getter works
        self.assertEquals({'body': "Hello World"}, plugin.get_translatable_content())

        # change the content
        self.assertEquals(True, plugin.set_translatable_content({'body': "It works!"}))

        # check if it changed
        self.assertEquals("It works!", plugin.body)

        # double check through the getter
        self.assertEquals({'body': "It works!"}, plugin.get_translatable_content())


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
        page = create_page('testpage', 'nav_playground.html', 'en')
        body = page.placeholders.get(slot="body")
        plugin = File(
            plugin_type='FilePlugin',
            placeholder=body,
            position=1,
            language=settings.LANGUAGE_CODE,
        )
        plugin.file.save("UPPERCASE.JPG", SimpleUploadedFile("UPPERCASE.jpg", b"content"), False)
        plugin.insert_at(None, position='last-child', save=True)
        self.assertNotEquals(plugin.get_icon_url().find('jpg'), -1)


class PluginManyToManyTestCase(PluginsTestBaseCase):
    def setUp(self):
        self.super_user = User(username="test", is_staff=True, is_active=True, is_superuser=True)
        self.super_user.set_password("test")
        self.super_user.save()

        self.slave = User(username="slave", is_staff=True, is_active=True, is_superuser=False)
        self.slave.set_password("slave")
        self.slave.save()

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
        self.assertEquals(response.status_code, 200)
        pk = CMSPlugin.objects.all()[0].pk
        expected = {
            "url": "/en/admin/cms/page/edit-plugin/%s/" % pk,
            "breadcrumb": [
                {
                    "url": "/en/admin/cms/page/edit-plugin/%s/" % pk,
                    "title": "Articles"
                }
            ],
            'delete': '/en/admin/cms/page/delete-plugin/%s/' % pk
        }
        self.assertEquals(json.loads(response.content.decode('utf8')), expected)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + str(CMSPlugin.objects.all()[0].pk) + "/"
        response = self.client.get(edit_url)
        self.assertEquals(response.status_code, 200)
        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticlePluginModel.objects.count(), 1)
        plugin = ArticlePluginModel.objects.all()[0]
        self.assertEquals(self.section_count, plugin.sections.count())
        response = self.client.get('/en/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(plugin.sections.through._meta.db_table, 'manytomany_rel_articlepluginmodel_sections')


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
        self.assertEquals(response.status_code, 200)
        pk = CMSPlugin.objects.all()[0].pk
        expected = {
            "url": "/en/admin/cms/page/edit-plugin/%s/" % pk,
            "breadcrumb": [
                {
                    "url": "/en/admin/cms/page/edit-plugin/%s/" % pk,
                    "title": "Articles"
                }
            ],
            'delete': '/en/admin/cms/page/delete-plugin/%s/' % pk
        }
        self.assertEquals(json.loads(response.content.decode('utf8')), expected)

        # there should be only 1 plugin
        self.assertEquals(1, CMSPlugin.objects.all().count())

        articles_plugin_pk = CMSPlugin.objects.all()[0].pk
        self.assertEquals(articles_plugin_pk, CMSPlugin.objects.all()[0].pk)
        # now edit the plugin
        edit_url = URL_CMS_PLUGIN_EDIT + str(CMSPlugin.objects.all()[0].pk) + "/"

        data = {
            'title': "Articles Plugin 1",
            'sections': self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(1, ArticlePluginModel.objects.count())
        articles_plugin = ArticlePluginModel.objects.all()[0]
        self.assertEquals(u'Articles Plugin 1', articles_plugin.title)
        self.assertEquals(self.section_count, articles_plugin.sections.count())


        # check publish box
        page = publish_page(page, self.super_user, 'en')

        # there should now be two plugins - 1 draft, 1 public
        self.assertEquals(2, CMSPlugin.objects.all().count())
        self.assertEquals(2, ArticlePluginModel.objects.all().count())

        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
        expected = [self.section_count for i in range(len(db_counts))]
        self.assertEqual(expected, db_counts)


    def test_copy_plugin_with_m2m(self):
        page = create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')

        plugin = ArticlePluginModel(
            plugin_type='ArticlePlugin',
            placeholder=placeholder,
            position=1,
            language=self.FIRST_LANG)
        plugin.insert_at(None, position='last-child', save=True)

        edit_url = URL_CMS_PLUGIN_EDIT + str(plugin.pk) + "/"

        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(edit_url, data)
        self.assertEquals(response.status_code, 200)
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

        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 0)
        self.assertEquals(CMSPlugin.objects.count(), 1)
        self.assertEquals(Page.objects.all().count(), 1)
        copy_data = {
            'source_placeholder_id': placeholder.pk,
            'target_placeholder_id': placeholder.pk,
            'target_language': self.SECOND_LANG,
            'source_language': self.FIRST_LANG,
        }
        response = self.client.post(URL_CMS_PAGE + "copy-plugins/", copy_data)
        self.assertEquals(response.status_code, 200)
        self.assertEqual(response.content.decode('utf8').count('"position":'), 1)
        # assert copy success
        self.assertEquals(CMSPlugin.objects.filter(language=self.FIRST_LANG).count(), 1)
        self.assertEquals(CMSPlugin.objects.filter(language=self.SECOND_LANG).count(), 1)
        self.assertEquals(CMSPlugin.objects.count(), 2)
        db_counts = [plugin.sections.count() for plugin in ArticlePluginModel.objects.all()]
        expected = [self.section_count for i in range(len(db_counts))]
        self.assertEqual(expected, db_counts)


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
        self.assertEquals(link.target, '')

    def test_open_in_blank_window(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': '_blank'})
        link = form.save()
        self.assertEquals(link.target, '_blank')

    def test_open_in_parent_window(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': '_parent'})
        link = form.save()
        self.assertEquals(link.target, '_parent')

    def test_open_in_top_window(self):
        form = LinkForm({'name': 'Linkname',
            'url': 'http://www.nonexistant.test', 'target': '_top'})
        link = form.save()
        self.assertEquals(link.target, '_top')

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
        # TODO: Django tests seem to leak models from test methods, somehow
        # we should clear django.db.models.loading.app_cache in tearDown.
        plugin_class = PluginModelBase('TestPlugin', (CMSPlugin,), {'__module__': 'cms.tests.plugins'})
        self.assertEqual(plugin_class._meta.db_table, 'tests_testplugin')

    def test_db_table_hack_with_mixin(self):
        class LeftMixin: pass

        class RightMixin: pass

        plugin_class = PluginModelBase('TestPlugin2', (LeftMixin, CMSPlugin, RightMixin),
                                       {'__module__': 'cms.tests.plugins'})
        self.assertEqual(plugin_class._meta.db_table, 'tests_testplugin2')

    def test_pickle(self):
        text = Text()
        a = text.__reduce__()


class PicturePluginTests(PluginsTestBaseCase):
    def test_link_or_page(self):
        """Test a validator: you can enter a url or a page_link, but not both."""

        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
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
        apps = ['cms.test_utils.project.brokenpluginapp']
        with SettingsOverride(INSTALLED_APPS=apps):
            plugin_pool.discovered = False
            self.assertRaises(ImportError, plugin_pool.discover_plugins)
