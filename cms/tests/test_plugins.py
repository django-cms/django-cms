# -*- coding: utf-8 -*-
from contextlib import contextmanager
import datetime
import pickle
import warnings

from cms.api import create_page

from django import http
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple, RelatedFieldWidgetWrapper
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Media
from django.test.testcases import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import override as force_language

from cms import api
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
    CMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_ADD,
    URL_CMS_PLUGIN_ADD, URL_CMS_PAGE_CHANGE,
    URL_CMS_PAGE_PUBLISH,
)
from cms.test_utils.util.fuzzy_int import FuzzyInt
from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.plugins import get_plugins
from django.utils.http import urlencode

from djangocms_text_ckeditor.models import Text
from djangocms_text_ckeditor.utils import plugin_to_tag


@contextmanager
def register_plugins(*plugins):
    for plugin in plugins:
        plugin_pool.register_plugin(plugin)

    # clear cached properties
    plugin_pool._clear_cached()

    try:
        yield
    finally:
        for plugin in plugins:
            plugin_pool.unregister_plugin(plugin)


def _render_placeholder(placeholder, context, **kwargs):
    request = context['request']
    toolbar = get_toolbar_from_request(request)
    content_renderer = toolbar.content_renderer
    return content_renderer.render_placeholder(placeholder, context, **kwargs)


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
        plugin_pool._clear_cached()
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

    def get_placeholder(self):
        return Placeholder.objects.create(slot='test')


class PluginsTestCase(PluginsTestBaseCase):

    def _create_link_plugin_on_page(self, page, slot='col_left'):
        add_url = self.get_add_plugin_uri(
            placeholder=page.placeholders.get(slot=slot),
            plugin_type='LinkPlugin',
            language=settings.LANGUAGES[0][0],
        )
        data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 200)
        return CMSPlugin.objects.latest('pk').pk

    def __edit_link_plugin(self, plugin_id, text):
        endpoint = self.get_admin_url(Page, 'edit_plugin', plugin_id)
        endpoint += '?cms_path=/en/'

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)
        data = {'name': text, 'external_link': 'https://www.django-cms.org'}
        response = self.client.post(endpoint, data)
        self.assertEqual(response.status_code, 200)
        return CMSPlugin.objects.get(pk=plugin_id).get_bound_plugin()

    def test_add_edit_plugin(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.drafts().first()
        created_plugin_id = self._create_link_plugin_on_page(page)
        # now edit the plugin
        plugin = self.__edit_link_plugin(created_plugin_id, "Hello World")
        self.assertEqual("Hello World", plugin.name)

    def test_plugin_add_form_integrity(self):
        admin.autodiscover()
        admin_instance = admin.site._registry[ArticlePluginModel]
        placeholder = self.get_placeholder()
        url = URL_CMS_PLUGIN_ADD + '?' + urlencode({
            'plugin_type': "ArticlePlugin",
            'target_language': settings.LANGUAGES[0][0],
            'placeholder_id': placeholder.pk,
        })
        superuser = self.get_superuser()
        plugin = plugin_pool.get_plugin('ArticlePlugin')

        with self.login_user_context(superuser):
            request = self.get_request(url)
            PluginFormClass = plugin(
                model=plugin.model,
                admin_site=admin.site,
            ).get_form(request)
            plugin_fields = list(PluginFormClass.base_fields.keys())

            OriginalFormClass = admin_instance.get_form(request)
            original_fields = list(OriginalFormClass.base_fields.keys())

            # Assert both forms have the same fields
            self.assertEqual(plugin_fields, original_fields)

            # Now assert the plugin form has the related field wrapper
            # widget on the sections field.
            self.assertIsInstance(
                PluginFormClass.base_fields['sections'].widget,
                RelatedFieldWidgetWrapper,
            )

            # Now assert the admin form has the related field wrapper
            # widget on the sections field.
            self.assertIsInstance(
                OriginalFormClass.base_fields['sections'].widget,
                RelatedFieldWidgetWrapper,
            )

            # Now assert the plugin form has the filtered select multiple
            # widget wrapped by the related field wrapper
            self.assertIsInstance(
                PluginFormClass.base_fields['sections'].widget.widget,
                FilteredSelectMultiple,
            )

            # Now assert the admin form has the filtered select multiple
            # widget wrapped by the related field wrapper
            self.assertIsInstance(
                OriginalFormClass.base_fields['sections'].widget.widget,
                FilteredSelectMultiple,
            )

    def test_excluded_plugin(self):
        """
        Test that you can't add a text plugin
        """

        CMS_PLACEHOLDER_CONF = {
            'body': {
                'excluded_plugins': ['TextPlugin']
            }
        }

        # try to add a new text plugin
        with self.settings(CMS_PLACEHOLDER_CONF=CMS_PLACEHOLDER_CONF):
            page_data = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.drafts().first()
            installed_plugins = plugin_pool.get_all_plugins('body', page)
            installed_plugins = [cls.__name__ for cls in installed_plugins]
            self.assertNotIn('TextPlugin', installed_plugins)

        CMS_PLACEHOLDER_CONF = {
            'body': {
                'plugins': ['TextPlugin'],
                'excluded_plugins': ['TextPlugin']
            }
        }

        # try to add a new text plugin
        with self.settings(CMS_PLACEHOLDER_CONF=CMS_PLACEHOLDER_CONF):
            page_data = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.drafts().first()
            installed_plugins = plugin_pool.get_all_plugins('body', page)
            installed_plugins = [cls.__name__ for cls in installed_plugins]
            self.assertNotIn('TextPlugin', installed_plugins)

    def test_plugin_edit_marks_page_dirty(self):
        page_data = self.get_new_page_data()
        response = self.client.post(URL_CMS_PAGE_ADD, page_data)
        self.assertEqual(response.status_code, 302)
        page = Page.objects.drafts().first()
        response = self.client.post(URL_CMS_PAGE_PUBLISH % (page.pk, 'en'))
        self.assertEqual(response.status_code, 302)
        created_plugin_id = self._create_link_plugin_on_page(page)
        page = Page.objects.drafts().first()
        self.assertEqual(page.is_dirty('en'), True)
        response = self.client.post(URL_CMS_PAGE_PUBLISH % (page.pk, 'en'))
        self.assertEqual(response.status_code, 302)
        page = Page.objects.drafts().first()
        self.assertEqual(page.is_dirty('en'), False)
        self.__edit_link_plugin(created_plugin_id, "Hello World")
        page = Page.objects.drafts().first()
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
            context = self.get_context(page_en.get_absolute_url(), page=page_en)
            rendered_placeholder = _render_placeholder(ph_en, context)
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
            'target_language': 'en',
            'plugin_order[]': [text_plugin_1.id, text_plugin_2.id, text_plugin_3.id],
        }

        endpoint = self.get_move_plugin_uri(text_plugin_1)

        self.client.post(endpoint, data)

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
            draft_page_context = self.get_context(draft_page.get_absolute_url(), page=draft_page)
            rendered_placeholder = _render_placeholder(placeholder, draft_page_context)
            self.assertEqual(rendered_placeholder, "I'm the firstI'm the secondI'm the third")
            live_page_context = self.get_context(live_page.get_absolute_url(), page=live_page)
            rendered_live_placeholder = _render_placeholder(live_placeholder, live_page_context)
            self.assertEqual(rendered_live_placeholder, "I'm the firstI'm the secondI'm the third")

        columns = api.add_plugin(placeholder, "MultiColumnPlugin", "en")
        column = api.add_plugin(
            placeholder,
            "ColumnPlugin",
            "en",
            target=columns,
        )

        data = {
            'placeholder_id': placeholder.id,
            'plugin_id': text_plugin_1.id,
            'plugin_parent': '',
            'target_language': 'en',
            'plugin_order[]': [
                text_plugin_1.id,
                text_plugin_2.id,
                text_plugin_3.id,
                columns.id,
                column.id,
            ],
        }
        response = self.client.post(endpoint, data)
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            'order parameter references plugins in different trees',
            status_code=400,
        )

    def test_plugin_breadcrumbs(self):
        """
        Test the plugin breadcrumbs order
        """
        draft_page = api.create_page("home", "col_two.html", "en",
                                     slug="page1", published=False, in_navigation=True)
        placeholder = draft_page.placeholders.get(slot="col_left")

        columns = api.add_plugin(placeholder, "MultiColumnPlugin", "en")
        column = api.add_plugin(placeholder, "ColumnPlugin", "en", target=columns)
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

    def test_add_text_plugin_empty_tag(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page = api.create_page(
            title='test page',
            template='nav_playground.html',
            language=settings.LANGUAGES[0][0],
        )
        plugin = api.add_plugin(
            placeholder=page.placeholders.get(slot='body'),
            plugin_type='TextPlugin',
            language=settings.LANGUAGES[0][0],
            body='<div class="someclass"></div><p>foo</p>'
        )
        self.assertEqual(plugin.body, '<div class="someclass"></div><p>foo</p>')

    def test_add_text_plugin_html_sanitizer(self):
        """
        Test that you can add a text plugin
        """
        # add a new text plugin
        page = api.create_page(
            title='test page',
            template='nav_playground.html',
            language=settings.LANGUAGES[0][0],
        )
        plugin = api.add_plugin(
            placeholder=page.placeholders.get(slot='body'),
            plugin_type='TextPlugin',
            language=settings.LANGUAGES[0][0],
            body='<script>var bar="hacked"</script>'
        )
        self.assertEqual(
            plugin.body,
            '&lt;script&gt;var bar="hacked"&lt;/script&gt;'
        )

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
                                        name="A Link", external_link="https://www.django-cms.org")
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
                self.assertTrue('Link - A Link' in plugin.body)
                self.assertTrue('id="%s"' % plugin.get_children()[0].pk in plugin.body)
                self.assertTrue('Link - A Link' in new_plugins[idx].body)
                self.assertTrue('id="%s"' % new_plugins[idx].get_children()[0].pk in new_plugins[idx].body)

    def test_plugin_position(self):
        page_en = api.create_page("CopyPluginTestPage (EN)", "nav_playground.html", "en")
        placeholder = page_en.placeholders.get(slot="body")  # ID 2
        placeholder_right = page_en.placeholders.get(slot="right-column")
        columns = api.add_plugin(placeholder, "MultiColumnPlugin", "en")  # ID 1
        column_1 = api.add_plugin(placeholder, "ColumnPlugin", "en", target=columns)  # ID 2
        column_2 = api.add_plugin(placeholder, "ColumnPlugin", "en", target=columns)  # ID 3
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
                                        name="A Link", external_link="https://www.django-cms.org")

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
        self.assertEqual(link_plugin_de.external_link, link_plugin_en.external_link)

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
            external_link="https://www.django-cms.org"
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
        page = api.create_page(
             title='test page',
            language=settings.LANGUAGES[0][0],
            template='nav_playground.html'
        )
        plugin = api.add_plugin(
            placeholder=page.placeholders.get(slot='body'),
            language='en',
            plugin_type='TextPlugin',
            body=''
        )
        # there should be only 1 plugin
        self.assertEqual(CMSPlugin.objects.all().count(), 1)

        # delete the plugin
        plugin_data = {
            'plugin_id': plugin.pk
        }

        endpoint = self.get_admin_url(Page, 'delete_plugin', plugin.pk)
        endpoint += '?cms_path=/en/'

        response = self.client.post(endpoint, plugin_data)
        self.assertEqual(response.status_code, 302)
        # there should be no plugins
        self.assertEqual(0, CMSPlugin.objects.all().count())

    def test_remove_plugin_after_published(self):
        # add a page
        page = api.create_page("home", "nav_playground.html", "en")

        # add a plugin
        plugin = api.add_plugin(
            placeholder=page.placeholders.get(slot='body'),
            plugin_type='TextPlugin',
            language=settings.LANGUAGES[0][0],
            body=''
        )
        # there should be only 1 plugin
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        self.assertEqual(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=True).count(), 1)

        # publish page
        response = self.client.post(URL_CMS_PAGE + "%d/en/publish/" % page.pk, {1: 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Page.objects.count(), 2)

        # there should now be two plugins - 1 draft, 1 public
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

        # delete the plugin
        plugin_data = {
            'plugin_id': plugin.pk
        }

        endpoint = self.get_admin_url(Page, 'delete_plugin', plugin.pk)
        endpoint += '?cms_path=/en/'

        response = self.client.post(endpoint, plugin_data)
        self.assertEqual(response.status_code, 302)

        # there should be no plugins
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        self.assertEqual(CMSPlugin.objects.filter(placeholder__page__publisher_is_draft=False).count(), 1)

    def test_remove_plugin_not_associated_to_page(self):
        """
        Test case for PlaceholderField
        """
        page = api.create_page(
            title='test page',
            template='nav_playground.html',
            language='en'
        )
        # add a plugin
        plugin = api.add_plugin(
            placeholder=page.placeholders.get(slot='body'),
            plugin_type='TextPlugin',
            language=settings.LANGUAGES[0][0],
            body=''
        )
        # there should be only 1 plugin
        self.assertEqual(CMSPlugin.objects.all().count(), 1)

        ph = Placeholder(slot="subplugin")
        ph.save()
        url = URL_CMS_PLUGIN_ADD + '?' + urlencode({
            'plugin_type': "TextPlugin",
            'target_language': settings.LANGUAGES[0][0],
            'placeholder': ph.pk,
            'plugin_parent': plugin.pk

        })
        response = self.client.post(url, {'body': ''})
        # no longer allowed for security reasons
        self.assertEqual(response.status_code, 400)

    def test_register_plugin_twice_should_raise(self):
        number_of_plugins_before = len(plugin_pool.registered_plugins)
        # The first time we register the plugin is should work
        with register_plugins(DumbFixturePlugin):
            # Let's add it a second time. We should catch and exception
            raised = False
            try:
                plugin_pool.register_plugin(DumbFixturePlugin)
            except PluginAlreadyRegistered:
                raised = True
            self.assertTrue(raised)
        # Let's make sure we have the same number of plugins as before:
        number_of_plugins_after = len(plugin_pool.registered_plugins)
        self.assertEqual(number_of_plugins_before, number_of_plugins_after)

    def test_unregister_non_existing_plugin_should_raise(self):
        number_of_plugins_before = len(plugin_pool.registered_plugins)
        raised = False
        try:
            # There should not be such a plugin registered if the others tests
            # don't leak plugins
            plugin_pool.unregister_plugin(DumbFixturePlugin)
        except PluginNotRegistered:
            raised = True
        self.assertTrue(raised)
        # Let's count, to make sure we didn't remove a plugin accidentally.
        number_of_plugins_after = len(plugin_pool.registered_plugins)
        self.assertEqual(number_of_plugins_before, number_of_plugins_after)

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
        out = _render_placeholder(placeholder, self.get_context(), width=300)
        self.assertFalse(len(out))
        self.assertFalse(len(placeholder._plugins_cache))

    def test_repr(self):
        non_saved_plugin = CMSPlugin()
        self.assertIsNone(non_saved_plugin.pk)
        self.assertIn('id=None', repr(non_saved_plugin))
        self.assertIn("plugin_type=''", repr(non_saved_plugin))

        saved_plugin = CMSPlugin.objects.create(plugin_type='TextPlugin')
        self.assertIn('id={}'.format(saved_plugin.pk), repr(saved_plugin))
        self.assertIn("plugin_type='{}'".format(saved_plugin.plugin_type), repr(saved_plugin))


    def test_pickle(self):
        page = api.create_page("page", "nav_playground.html", "en")
        placeholder = page.placeholders.get(slot='body')
        text_plugin = api.add_plugin(
            placeholder,
            "TextPlugin",
            'en',
            body="Hello World",
        )
        cms_plugin = text_plugin.cmsplugin_ptr

        # assert we can pickle and unpickle a solid plugin (subclass)
        self.assertEqual(text_plugin, pickle.loads(pickle.dumps(text_plugin)))

        # assert we can pickle and unpickle a cms plugin (parent)
        self.assertEqual(cms_plugin, pickle.loads(pickle.dumps(cms_plugin)))

    def test_defer_pickle(self):
        page = api.create_page("page", "nav_playground.html", "en")

        placeholder = page.placeholders.get(slot='body')
        api.add_plugin(placeholder, "TextPlugin", 'en', body="Hello World")
        plugins = Text.objects.all().defer('path')
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

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            a.page
            self.assertEqual(1, len(w))
            self.assertIn('test_plugins.py', w[0].filename)

    def test_editing_plugin_changes_page_modification_time_in_sitemap(self):
        now = timezone.now()
        one_day_ago = now - datetime.timedelta(days=1)
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        title = page.get_title_obj('en')
        page.creation_date = one_day_ago
        page.changed_date = one_day_ago
        plugin_id = self._create_link_plugin_on_page(page, slot='body')
        plugin = self.__edit_link_plugin(plugin_id, "fnord")

        actual_last_modification_time = CMSSitemap().lastmod(title)
        actual_last_modification_time -= datetime.timedelta(microseconds=actual_last_modification_time.microsecond)
        self.assertEqual(plugin.changed_date.date(), actual_last_modification_time.date())

    def test_moving_plugin_to_different_placeholder(self):
        with register_plugins(DumbFixturePlugin):
            page = api.create_page(
                "page",
                "nav_playground.html",
                "en"
            )
            plugin = api.add_plugin(
                placeholder=page.placeholders.get(slot='body'),
                plugin_type='DumbFixturePlugin',
                language=settings.LANGUAGES[0][0]
            )
            child_plugin = api.add_plugin(
                placeholder=page.placeholders.get(slot='body'),
                plugin_type='DumbFixturePlugin',
                language=settings.LANGUAGES[0][0],
                parent=plugin
            )
            post = {
                'plugin_id': child_plugin.pk,
                'placeholder_id': page.placeholders.get(slot='right-column').pk,
                'target_language': 'en',
                'plugin_parent': '',
            }

            endpoint = self.get_move_plugin_uri(child_plugin)
            response = self.client.post(endpoint, post)
            self.assertEqual(response.status_code, 200)

            from cms.utils.plugins import build_plugin_tree
            build_plugin_tree(page.placeholders.get(slot='right-column').get_plugins_list())

    def test_custom_plugin_urls(self):
        plugin_url = reverse('admin:dumbfixtureplugin')

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

        with register_plugins(ParentRequiredPlugin):
            page = api.create_page("page", "nav_playground.html", "en", published=True)
            placeholder = page.placeholders.get(slot='body')

            plugin_list = plugin_pool.get_all_plugins(placeholder=placeholder, page=page)
            self.assertFalse(ParentRequiredPlugin in plugin_list)

    def test_plugin_toolbar_struct(self):
        # Tests that the output of the plugin toolbar structure.
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')

        from cms.utils.placeholder import get_toolbar_plugin_struct

        expected_struct_en = {
            'module': u'Generic',
            'name': u'Style',
            'value': 'StylePlugin',
        }

        expected_struct_de = {
            'module': u'Generisch',
            'name': u'Style',
            'value': 'StylePlugin',
        }

        toolbar_struct = get_toolbar_plugin_struct(
            plugins=plugin_pool.registered_plugins,
            slot=placeholder.slot,
            page=page,
        )

        style_config = [config for config in toolbar_struct if config['value'] == 'StylePlugin']

        self.assertEqual(len(style_config), 1)

        style_config = style_config[0]

        with force_language('en'):
            self.assertEqual(force_text(style_config['module']), expected_struct_en['module'])
            self.assertEqual(force_text(style_config['name']), expected_struct_en['name'])

        with force_language('de'):
            self.assertEqual(force_text(style_config['module']), expected_struct_de['module'])
            self.assertEqual(force_text(style_config['name']), expected_struct_de['name'])

    def test_plugin_toolbar_struct_permissions(self):
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.placeholders.get(slot='body')
        page_url = page.get_absolute_url() + '?' + get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')

        with self.login_user_context(staff_user):
            request = self.get_request(page_url, page=page)
            request.toolbar = CMSToolbar(request)
            renderer = self.get_structure_renderer(request=request)
            output = renderer.render_placeholder(placeholder, language='en', page=page)
            self.assertIn('<a data-rel="add" href="TextPlugin">Text</a>', output)
            self.assertNotIn('<a data-rel="add" href="LinkPlugin">Link</a>', output)

    def test_plugin_child_classes_from_settings(self):
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ChildClassesPlugin = type('ChildClassesPlugin', (CMSPluginBase,),
                                    dict(child_classes=['TextPlugin'], render_template='allow_children_plugin.html'))

        with register_plugins(ChildClassesPlugin):
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

    def test_plugin_parent_classes_from_settings(self):
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ParentClassesPlugin = type('ParentClassesPlugin', (CMSPluginBase,),
                                    dict(parent_classes=['TextPlugin'], render_plugin=False))

        with register_plugins(ParentClassesPlugin):
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

    def test_plugin_parent_classes_from_object(self):
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ParentPlugin = type('ParentPlugin', (CMSPluginBase,),
                                    dict(render_plugin=False))
        ChildPlugin = type('ChildPlugin', (CMSPluginBase,),
                                    dict(parent_classes=['ParentPlugin'], render_plugin=False))

        with register_plugins(ParentPlugin, ChildPlugin):
            plugin = api.add_plugin(placeholder, ParentPlugin, settings.LANGUAGES[0][0])
            plugin = plugin.get_plugin_class_instance()
            ## assert baseline
            child_classes = plugin.get_child_classes(placeholder.slot, page)
            self.assertIn('ChildPlugin', child_classes)
            self.assertIn('ParentPlugin', child_classes)

    def test_plugin_require_parent_from_object(self):
        page = api.create_page("page", "nav_playground.html", "en", published=True)
        placeholder = page.placeholders.get(slot='body')
        ParentPlugin = type('ParentPlugin', (CMSPluginBase,),
                                    dict(render_plugin=False))
        ChildPlugin = type('ChildPlugin', (CMSPluginBase,),
                                    dict(require_parent=True, render_plugin=False))

        with register_plugins(ParentPlugin, ChildPlugin):
            plugin = api.add_plugin(placeholder, ParentPlugin, settings.LANGUAGES[0][0])
            plugin = plugin.get_plugin_class_instance()
            ## assert baseline
            child_classes = plugin.get_child_classes(placeholder.slot, page)
            self.assertIn('ChildPlugin', child_classes)
            self.assertIn('ParentPlugin', child_classes)

    def test_plugin_pool_register_returns_plugin_class(self):
        @plugin_pool.register_plugin
        class DecoratorTestPlugin(CMSPluginBase):
            render_plugin = False
            name = "Test Plugin"
        self.assertIsNotNone(DecoratorTestPlugin)


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
        context = self.get_context(path=page_en.get_absolute_url())
        request = context['request']
        plugins = get_plugins(request, ph_en, page_en.template)
        content_renderer = self.get_content_renderer()

        for plugin in plugins:
            if plugin.title == 'custom template':
                content = content_renderer.render_plugin(plugin, context, ph_en)
                self.assertEqual(plugin.get_plugin_class_instance().get_render_template({}, plugin, ph_en), 'articles_custom.html')
                self.assertTrue('Articles Custom template' in content)
            else:
                content = content_renderer.render_plugin(plugin, context, ph_en)
                self.assertEqual(plugin.get_plugin_class_instance().get_render_template({}, plugin, ph_en), 'articles.html')
                self.assertFalse('Articles Custom template' in content)

    def test_add_plugin_with_m2m(self):
        # add a new text plugin
        self.assertEqual(ArticlePluginModel.objects.count(), 0)
        page_data = self.get_new_page_data()
        self.client.post(URL_CMS_PAGE_ADD, page_data)
        page = Page.objects.drafts().first()
        page.publish('en')
        placeholder = page.placeholders.get(slot='col_left')
        add_url = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='ArticlePlugin',
            language=self.FIRST_LANG,
        )
        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(add_url, data)
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
        page = Page.objects.drafts().first()
        placeholder = page.placeholders.get(slot='col_left')

        # add a plugin
        data = {
            'title': "Articles Plugin 1",
            'sections': self.section_pks
        }

        add_url = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='ArticlePlugin',
            language=self.FIRST_LANG,
        )

        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/cms/page/plugin/confirm_form.html')

        # there should be only 1 plugin
        self.assertEqual(1, CMSPlugin.objects.all().count())
        self.assertEqual(1, ArticlePluginModel.objects.count())
        articles_plugin = ArticlePluginModel.objects.all()[0]
        self.assertEqual(u'Articles Plugin 1', articles_plugin.title)
        self.assertEqual(self.section_count, articles_plugin.sections.count())

        # check publish box
        api.publish_page(page, self.super_user, 'en')

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

        endpoint = self.get_admin_url(Page, 'edit_plugin', plugin.pk)
        endpoint += '?cms_path=/{}/'.format(self.FIRST_LANG)

        data = {
            'title': "Articles Plugin 1",
            "sections": self.section_pks
        }
        response = self.client.post(endpoint, data)
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
        self.assertRedirects(response, URL_CMS_PAGE + "?language=%s" % self.SECOND_LANG)

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

        endpoint = self.get_admin_url(Page, 'copy_plugins')
        endpoint += '?cms_path=/{}/'.format(self.FIRST_LANG)

        response = self.client.post(endpoint, copy_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf8').count('"plugin_type": "ArticlePlugin"'), 1)
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


class NoDatabasePluginTests(TestCase):

    def get_plugin_model(self, plugin_type):
        return plugin_pool.get_plugin(plugin_type).model

    def test_render_meta_is_unique(self):
        text = self.get_plugin_model('TextPlugin')
        link = self.get_plugin_model('LinkPlugin')
        self.assertNotEqual(id(text._render_meta), id(link._render_meta))

    def test_render_meta_does_not_leak(self):
        text = self.get_plugin_model('TextPlugin')
        link = self.get_plugin_model('LinkPlugin')

        text._render_meta.text_enabled = False
        link._render_meta.text_enabled = False

        self.assertFalse(text._render_meta.text_enabled)
        self.assertFalse(link._render_meta.text_enabled)

        link._render_meta.text_enabled = True

        self.assertFalse(text._render_meta.text_enabled)
        self.assertTrue(link._render_meta.text_enabled)

    def test_db_table_hack(self):
        # Plugin models have been moved away due to Django's AppConfig
        from cms.test_utils.project.bunch_of_plugins.models import TestPlugin1
        self.assertEqual(TestPlugin1._meta.db_table, 'bunch_of_plugins_testplugin1')

    def test_db_table_hack_with_mixin(self):
        # Plugin models have been moved away due to Django's AppConfig
        from cms.test_utils.project.bunch_of_plugins.models import TestPlugin2
        self.assertEqual(TestPlugin2._meta.db_table, 'bunch_of_plugins_testplugin2')


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
        page = create_page("Test", "nav_playground.html", settings.LANGUAGES[0][0])
        placeholder = page.placeholders.get(slot='body')

        # Add the MTI plugin
        add_url = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='TestPluginBeta',
            language=settings.LANGUAGES[0][0],
        )

        data = {
            'alpha': 'ALPHA',
            'beta': 'BETA'
        }
        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TestPluginBetaModel.objects.count(), 1)
        plugin_model = TestPluginBetaModel.objects.all()[0]
        self.assertEqual("ALPHA", plugin_model.alpha)
        self.assertEqual("BETA", plugin_model.beta)

    def test_related_name(self):
        from cms.test_utils.project.mti_pluginapp.models import (
            TestPluginAlphaModel, TestPluginBetaModel, ProxiedAlphaPluginModel,
            ProxiedBetaPluginModel, AbstractPluginParent, TestPluginGammaModel, MixedPlugin,
            LessMixedPlugin, NonPluginModel
        )
        # the first concrete class of the following four plugins is TestPluginAlphaModel
        self.assertEqual(TestPluginAlphaModel.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_testpluginalphamodel')
        self.assertEqual(TestPluginBetaModel.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_testpluginalphamodel')
        self.assertEqual(ProxiedAlphaPluginModel.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_testpluginalphamodel')
        self.assertEqual(ProxiedBetaPluginModel.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_testpluginalphamodel')
        # Abstract plugins will have the dynamic format for related name
        self.assertEqual(
            AbstractPluginParent.cmsplugin_ptr.field.remote_field.related_name,
            '%(app_label)s_%(class)s'
        )
        # Concrete plugin of an abstract plugin gets its relatedname
        self.assertEqual(TestPluginGammaModel.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_testplugingammamodel')
        # Child plugin gets it's own related name
        self.assertEqual(MixedPlugin.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_mixedplugin')
        # If the child plugin inherit straight from CMSPlugin, even if composed with
        # other models, gets its own related_name
        self.assertEqual(LessMixedPlugin.cmsplugin_ptr.field.remote_field.related_name,
                         'mti_pluginapp_lessmixedplugin')
        # Non plugins are skipped
        self.assertFalse(hasattr(NonPluginModel, 'cmsplugin_ptr'))
