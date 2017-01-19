# -*- coding: utf-8 -*-
from collections import defaultdict

from django.template import Template

from cms import api
from cms.cms_plugins import AliasPlugin
from cms.models import Placeholder, AliasPluginModel
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.urlutils import admin_reverse

from sekizai.data import UniqueSequence
from sekizai.helpers import get_varname


class AliasTestCase(CMSTestCase):

    def _get_example_obj(self):
        obj = Example1.objects.create(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        return obj

    def test_add_plugin_alias(self):
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        with self.login_user_context(self.get_superuser()):
            response = self.client.post(admin_reverse('cms_create_alias'), data={'plugin_id': text_plugin_1.pk})
            self.assertEqual(response.status_code, 200)
            response = self.client.post(admin_reverse('cms_create_alias'), data={'placeholder_id': ph_en.pk})
            self.assertEqual(response.status_code, 200)
            response = self.client.post(admin_reverse('cms_create_alias'))
            self.assertEqual(response.status_code, 400)
            response = self.client.post(admin_reverse('cms_create_alias'), data={'plugin_id': 20000})
            self.assertEqual(response.status_code, 400)
            response = self.client.post(admin_reverse('cms_create_alias'), data={'placeholder_id': 20000})
            self.assertEqual(response.status_code, 400)
        response = self.client.post(admin_reverse('cms_create_alias'), data={'plugin_id': text_plugin_1.pk})
        self.assertEqual(response.status_code, 403)
        instance = AliasPluginModel.objects.all()[0]
        admin = AliasPlugin()
        context = self.get_context()
        admin.render(context, instance, ph_en)
        self.assertEqual(context['content'], "I'm the first")

    def test_alias_recursion(self):
        page_en = api.create_page(
            "Alias plugin",
            "col_two.html",
            "en",
            slug="page1",
            published=True,
            in_navigation=True,
        )
        ph_1_en = page_en.placeholders.get(slot="col_left")
        ph_2_en = page_en.placeholders.get(slot="col_sidebar")

        api.add_plugin(ph_1_en, 'StylePlugin', 'en', tag_type='div', class_name='info')
        api.add_plugin(ph_1_en, 'AliasPlugin', 'en', alias_placeholder=ph_2_en)
        api.add_plugin(ph_2_en, 'AliasPlugin', 'en', alias_placeholder=ph_1_en)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(page_en.get_absolute_url() + '?edit')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<div class="info">', html=True)

    def test_alias_placeholder_is_not_editable(self):
        """
        When a placeholder is aliased, it shouldn't render as editable
        in the structure mode.
        """
        source_page = api.create_page(
            "Home",
            "col_two.html",
            "en",
            published=True,
            in_navigation=True,
        )
        source_placeholder = source_page.placeholders.get(slot="col_left")

        style = api.add_plugin(
            source_placeholder,
            'StylePlugin',
            'en',
            tag_type='div',
            class_name='info',
        )

        target_page = api.create_page(
            "Target",
            "col_two.html",
            "en",
            published=True,
            in_navigation=True,
        )
        target_placeholder = target_page.placeholders.get(slot="col_left")
        alias = api.add_plugin(
            target_placeholder,
            'AliasPlugin',
            'en',
            alias_placeholder=source_placeholder,
        )

        with self.login_user_context(self.get_superuser()):
            context = self.get_context(path=target_page.get_absolute_url(), page=target_page)
            context['request'].toolbar = CMSToolbar(context['request'])
            context['request'].toolbar.edit_mode = True
            context[get_varname()] = defaultdict(UniqueSequence)

            content_renderer = context['cms_content_renderer']

            output = content_renderer.render_placeholder(
                target_placeholder,
                context=context,
                language='en',
                page=target_page,
                editable=True
            )

            tag_format = '<template class="cms-plugin cms-plugin-start cms-plugin-{}">'

            expected_plugins = [alias]
            unexpected_plugins = [style]

            for plugin in expected_plugins:
                start_tag = tag_format.format(plugin.pk)
                self.assertIn(start_tag, output)

            for plugin in unexpected_plugins:
                start_tag = tag_format.format(plugin.pk)
                self.assertNotIn(start_tag, output)

            editable_placeholders = content_renderer.get_rendered_editable_placeholders()
            self.assertNotIn(source_placeholder,editable_placeholders)

    def test_alias_from_page_change_form_text(self):
        superuser = self.get_superuser()
        api.create_page(
            "Home",
            "col_two.html",
            "en",
            published=True,
            in_navigation=True,
        )
        source_page = api.create_page(
            "Source",
            "col_two.html",
            "en",
            published=True,
            in_navigation=True,
        )
        source_placeholder = source_page.placeholders.get(slot="col_left")

        api.add_plugin(
            source_placeholder,
            'StylePlugin',
            'en',
            tag_type='div',
            class_name='info',
        )

        target_page = api.create_page(
            "Target",
            "col_two.html",
            "en",
            published=True,
            in_navigation=True,
        )
        target_placeholder = target_page.placeholders.get(slot="col_left")
        alias = api.add_plugin(
            target_placeholder,
            'AliasPlugin',
            'en',
            alias_placeholder=source_placeholder,
        )

        endpoint = self.get_change_plugin_uri(alias)

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            expected = ('This is an alias reference, you can edit the '
                        'content only on the <a href="/en/source/?edit" '
                        'target="_parent">Source</a> page.')
            self.assertContains(response, expected)

    def test_alias_from_generic_change_form_text(self):
        superuser = self.get_superuser()

        source_placeholder = self._get_example_obj().placeholder
        target_placeholder = self._get_example_obj().placeholder

        alias = api.add_plugin(
            target_placeholder,
            'AliasPlugin',
            'en',
            alias_placeholder=source_placeholder,
        )

        endpoint = self.get_change_plugin_uri(alias, container=Example1)

        with self.login_user_context(superuser):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            expected = 'There are no further settings for this plugin. Please press save.'
            self.assertContains(response, expected)

    def test_move_and_delete_plugin_alias(self):
        '''
        Test moving the plugin from the clipboard to a placeholder.
        '''
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        text_plugin_1 = api.add_plugin(ph_en, "TextPlugin", "en", body="I'm the first")
        with self.login_user_context(self.get_superuser()):
            #
            # Copies the placeholder to the clipboard...
            #
            self.client.post(admin_reverse('cms_create_alias'), data={'plugin_id': text_plugin_1.pk})

            #
            # Determine the copied plugins's ID. It should be in the special
            # 'clipboard' placeholder.
            #
            try:
                clipboard = Placeholder.objects.get(slot='clipboard')
            except (Placeholder.DoesNotExist, Placeholder.MultipleObjectsReturned):
                clipboard = 0

            self.assertGreater(clipboard.pk, 0)
            # The clipboard should only have a single plugin...
            self.assertEqual(len(clipboard.get_plugins_list()), 1)
            alias_plugin = clipboard.get_plugins_list()[0]

            copy_endpoint = self.get_copy_plugin_uri(alias_plugin)

            #
            # Test moving it from the clipboard to the page's placeholder...
            #
            response = self.client.post(copy_endpoint, data={
                'source_placeholder_id': clipboard.pk,
                'source_plugin': alias_plugin.pk,
                'source_language': 'en',
                'target_placeholder_id': ph_en.pk,
                'target_language': 'en',
            })
            self.assertEqual(response.status_code, 200)

            #
            # Now, test deleting the copy still on the clipboard...
            #
            delete_endpoint = self.get_delete_plugin_uri(alias_plugin)
            response = self.client.post(delete_endpoint, data={})
            self.assertEqual(response.status_code, 200)

    def test_context_menus(self):
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        context = self.get_context(page=page_en)
        context['placeholder'] = ph_en
        template = Template('{% load cms_tags %}{% render_extra_menu_items placeholder %}')
        output = template.render(context)
        self.assertTrue(len(output), 200)
