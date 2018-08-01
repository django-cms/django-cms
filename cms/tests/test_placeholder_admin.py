# -*- coding: utf-8 -*-
from django.forms.models import model_to_dict
from django.utils.http import urlencode

from cms.api import add_plugin, create_title
from cms.models import Placeholder, UserSettings, CMSPlugin
from cms.test_utils.testcases import CMSTestCase


class PlaceholderAdminTestCase(CMSTestCase):

    def test_add_plugin_endpoint(self):
        """
        Test that the Placeholder admin add_plugin endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot='test')
        plugins = placeholder.get_plugins('en').filter(plugin_type='TextPlugin')
        endpoint = self.get_admin_url(Placeholder, 'add_plugin')
        with self.login_user_context(superuser):
            endpoint = endpoint + '?' + urlencode({
                'plugin_type': "TextPlugin",
                'plugin_language': "en",
                'placeholder_id': placeholder.pk,
                'plugin_position': placeholder.get_next_plugin_position('en', insert_order='last')
            })
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(plugins.count(), 1)

    def test_copy_plugins_add_plugins_from_placeholder(self):
        """
        User can copy plugins from one placeholder to another
        """
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot='source')
        target_placeholder = Placeholder.objects.create(slot='target')
        source_plugin = add_plugin(
            source_placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_copy_plugin_uri(source_plugin, container=Placeholder, language="en")
        with self.login_user_context(superuser):
            data = {
                'source_language': "en",
                'source_placeholder_id': source_placeholder.pk,
                'target_language': "en",
                'target_placeholder_id': target_placeholder.pk,
            }
            response = self.client.post(endpoint, data)

        # Test that the target placeholder has the plugin copied from the source placeholder
        self.assertEqual(response.status_code, 200)
        self.assertTrue(source_placeholder.get_plugins('en').filter(pk=source_plugin.pk).exists())
        self.assertTrue(
            target_placeholder
                .get_plugins('en')
                .filter(plugin_type=source_plugin.plugin_type)
                .exists()
        )

    def test_copy_plugins_copy_plugin_to_clipboard(self):
        """
        User can copy plugins from a placeholder to the clipboard
        """
        superuser = self.get_superuser()
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        source_placeholder = Placeholder.objects.create(slot='source')
        source_plugin = add_plugin(
            source_placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_copy_plugin_uri(source_plugin, container=Placeholder, language="en")
        with self.login_user_context(superuser):
            data = {
                'source_language': "en",
                'source_placeholder_id': source_placeholder.pk,
                'source_plugin_id': source_plugin.pk,
                'target_language': "en",
                'target_placeholder_id': user_settings.clipboard.pk,
            }
            response = self.client.post(endpoint, data)

        # Test that the target placeholder has the plugin copied from the source placeholder
        self.assertEqual(response.status_code, 200)
        self.assertTrue(source_placeholder.get_plugins('en').filter(pk=source_plugin.pk).exists())
        self.assertTrue(
            user_settings.clipboard
                .get_plugins('en')
                .filter(plugin_type=source_plugin.plugin_type)
                .exists()
        )

    def test_copy_plugins_copy_placeholder_to_clipboard(self):
        """
        User can copy a placeholder to the clipboard
        """
        superuser = self.get_superuser()
        user_settings = UserSettings.objects.create(
            language="en",
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        source_placeholder = Placeholder.objects.create(slot='source')
        source_plugin = add_plugin(
            source_placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_copy_plugin_uri(source_plugin, container=Placeholder, language="en")
        with self.login_user_context(superuser):
            data = {
                'source_language': "en",
                'source_placeholder_id': source_placeholder.pk,
                'target_language': "en",
                'target_placeholder_id': user_settings.clipboard.pk,
            }
            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 200)

    def test_edit_plugin_endpoint(self):
        """
        Test that the Placeholder admin edit_plugins endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot='edit_plugin_placeholder')
        plugin = add_plugin(
            placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_admin_url(Placeholder, 'edit_plugin', plugin.pk)
        with self.login_user_context(superuser):
            data = model_to_dict(plugin, fields=['plugin_type', 'language', 'body'])
            data['body'] = 'Contents modified'
            response = self.client.post(endpoint, data)
            plugin.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(plugin.body, data['body'])

    def test_move_plugin_endpoint(self):
        """
        Test that the Placeholder admin move_plugin endpoint works

        TODO: Test??
            - _paste_placeholder
            - _paste_plugin
            - _cut_plugin
            - _move_plugin
        """
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot='source')
        target_placeholder = Placeholder.objects.create(slot='target')
        plugin = add_plugin(
            source_placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_admin_url(Placeholder, 'move_plugin')
        with self.login_user_context(superuser):
            data = {
                'plugin_id': plugin.pk,
                'target_language': 'en',
                'placeholder_id': target_placeholder.pk,
                'target_position': 1,
            }
            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
        self.assertFalse(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_delete_plugin_endpoint(self):
        """
        Test that the Placeholder admin delete_plugin endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot='source')
        plugin = add_plugin(
            placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_admin_url(Placeholder, 'delete_plugin', plugin.pk)
        with self.login_user_context(superuser):
            data = {'post': True}
            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_clear_placeholder_endpoint(self):
        """
        Test that the Placeholder admin delete_plugin endpoint works
        """
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot='source')
        add_plugin(
            placeholder,
            plugin_type="TextPlugin",
            language="en",
            body="Contents of the text plugin",
        )
        endpoint = self.get_admin_url(Placeholder, 'clear_placeholder', placeholder.pk)
        with self.login_user_context(superuser):
            response = self.client.post(endpoint, {'test': 0})

            self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)
