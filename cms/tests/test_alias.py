# -*- coding: utf-8 -*-
from cms import api
from cms.cms_plugins import AliasPlugin
from cms.models import Placeholder, AliasPluginModel
from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse
from django.template import Template, Context


class AliasTestCase(CMSTestCase):
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
        request = self.get_request("/")
        context = Context({'request': request})
        admin.render(context, instance, ph_en)
        self.assertEqual(context['content'], "I'm the first")

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

            #
            # Test moving it from the clipboard to the page's placeholder...
            #
            response = self.client.post(admin_reverse('cms_page_copy_plugins'), data={
                'source_placeholder_id': clipboard.pk,
                'source_plugin': alias_plugin.pk,
                'source_language': 'en',
                'target_placeholder_id': ph_en.pk,
                'target_language': 'en',
                # 'target_plugin_id': 0,
            })
            self.assertEqual(response.status_code, 200)

            #
            # Now, test deleting the copy still on the clipboard...
            #
            response = self.client.post(admin_reverse('cms_page_delete_plugin', args=[alias_plugin.pk]), data={})
            self.assertEqual(response.status_code, 200)

    def test_context_menus(self):
        page_en = api.create_page("PluginOrderPage", "col_two.html", "en",
                                  slug="page1", published=True, in_navigation=True)
        ph_en = page_en.placeholders.get(slot="col_left")
        class FakeRequest(object):
            current_page = page_en
            user = self.get_superuser()
            GET = {'language': 'en'}
            META = {"CSRF_COOKIE_USED": True}
        request = FakeRequest()
        template = Template('{% load cms_tags %}{% render_extra_menu_items placeholder %}')
        context = Context({'request': request})
        context['placeholder'] = ph_en
        output = template.render(context)
        self.assertTrue(len(output), 200)
