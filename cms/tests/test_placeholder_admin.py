# -*- coding: utf-8 -*-
from django.forms.models import model_to_dict
from django.utils.http import urlencode

from cms.api import add_plugin, create_page, create_title
from cms.models import Placeholder, UserSettings, CMSPlugin
from cms.test_utils.testcases import CMSTestCase

# TODO: Test permissions?
# TODO: Decide whether should have used get_change_plugin_uri to get the urls!!
# cms.tests.test_placeholder_admin.PlaceholderAdminTestCase.test_user_can_add_plugin
# cms.tests.test_placeholder_admin.PlaceholderAdminTestCase.test_user_can_edit_plugin


class PlaceholderAdminTestCase(CMSTestCase):

    def _add_plugin_to_page(self, page, plugin_type='LinkPlugin', language='en', publish=True):
        plugin_data = {
            'TextPlugin': {'body': '<p>text</p>'},
            'LinkPlugin': {'name': 'A Link', 'external_link': 'https://www.django-cms.org'},
        }
        placeholder = page.get_placeholders(language).get(slot='body')
        plugin = add_plugin(placeholder, plugin_type, language, **plugin_data[plugin_type])

        if publish:
            page.reload().publish(language)
        return plugin

    def _get_move_data(self, plugin, position, placeholder=None, parent=None):
        try:
            placeholder_id = placeholder.pk
        except AttributeError:
            placeholder_id = ''

        try:
            parent_id = parent.pk
        except AttributeError:
            parent_id = ''

        data = {
            'placeholder_id': placeholder_id,
            'target_language': 'en',
            'target_position': position,
            'plugin_id': plugin.pk,
            'plugin_parent': parent_id,
        }
        return data

    def _add_translation_to_page(self, page):
        translation = create_title(
            "de",
            "permissions-de",
            page.reload(),
            slug="permissions-de"
        )
        return translation

    def test_user_can_add_plugin(self):
        """
        User can add a new plugin if they have change permissions
        on the model attached to the placeholder and they have
        add permissions on the plugin model.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='TextPlugin')
        endpoint = self.get_admin_url(Placeholder, 'add_plugin')

        #FIXME: change_page, change_placeholder don't work
        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_placeholder')
        self.add_permission(staff_user, 'add_text')

        with self.login_user_context(staff_user):
            endpoint = endpoint + '?' + urlencode({
                'plugin_type': "TextPlugin",
                'plugin_language': "en",
                'placeholder_id': placeholder.pk,
                'plugin_position': placeholder.get_next_plugin_position('en', insert_order='last')
            })
            response = self.client.post(endpoint)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(plugins.count(), 1)

    def test_user_cant_add_plugin(self):
        """
        User can't add a new plugin if they do not have
        change permissions on the model attached to the placeholder
        and/or does not have add permissions on the plugin model.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        plugins = placeholder.get_plugins('en').filter(plugin_type='TextPlugin')
        endpoint = self.get_admin_url(Placeholder, 'add_plugin')

        # Test when change permission ont he container is not present
        self.add_permission(staff_user, 'add_placeholder')
        self.add_permission(staff_user, 'delete_placeholder')
        self.add_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            endpoint = endpoint + '?' + urlencode({
                'plugin_type': "TextPlugin",
                'plugin_language': "en",
                'placeholder_id': placeholder.pk,
                'plugin_position': placeholder.get_next_plugin_position('en', insert_order='last')
            })
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(plugins.count(), 0)

        # Test when plugin permission is removed
        self.add_permission(staff_user, 'change_placeholder')
        self.remove_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            endpoint = endpoint + '?' + urlencode({
                'plugin_type': "TextPlugin",
                'plugin_language': "en",
                'placeholder_id': placeholder.pk,
                'plugin_position': placeholder.get_next_plugin_position('en', insert_order='last')
            })
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(plugins.count(), 0)

    def test_user_can_edit_plugin(self):
        """
        User can edit a plugin if they have change permissions
        on the Page model, change permissions on the plugin model
        and global change permissions.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        plugin = self._add_plugin_to_page(page, language="en")
        endpoint = self.get_change_plugin_uri(plugin, container=placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'external_link'])
            data['name'] = 'A link 2'
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            plugin.refresh_from_db()
            self.assertEqual(plugin.name, data['name'])

    def test_user_cant_edit_plugin(self):
        """
        User can't edit a plugin if they
        do not have change permissions on the Page model,
        do not have change permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page, language="en")
        endpoint = self.get_change_plugin_uri(plugin, container=placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'external_link'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            plugin.refresh_from_db()
            self.assertNotEqual(plugin.name, data['name'])

    def test_user_can_delete_plugin(self):
        """
        User can delete a plugin if they have change permissions
        on the Page model, delete permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_delete_plugin_uri(plugin, container=placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            data = {'post': True}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertFalse(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_cant_delete_plugin(self):
        """
        User can't delete a plugin if they
        do not have change permissions on the Page model,
        do not have delete permissions on the plugin model
        and/or does not have global change permissions.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_delete_plugin_uri(plugin, container=placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'delete_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            data = {'post': True}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_can_move_plugin(self):
        """
        User can move a plugin if he has change permissions
        on the Page model, change permissions on the plugin model
        and global change permissions.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_move_plugin_uri(plugin, container=plugin.placeholder, language="en")
        source_placeholder = plugin.placeholder
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

        data = self._get_move_data(plugin, position=1, placeholder=target_placeholder)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertFalse(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_cant_move_plugin(self):
        """
        User can't move a plugin if he
        does not have change permissions on the Page model,
        does not have change permissions on the plugin model
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        endpoint = self.get_move_plugin_uri(plugin, container=plugin.placeholder, language="en")
        source_placeholder = plugin.placeholder
        target_placeholder = page.get_placeholders("en").get(slot='right-column')

        data = self._get_move_data(plugin, position=1, placeholder=target_placeholder)

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'change_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_can_copy_plugin(self):
        """
        User can copy a plugin if he has change permissions
        on the Page model, add permissions on the plugin model
        and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        translation = self._add_translation_to_page(page)
        endpoint = self.get_copy_plugin_uri(plugin, container=plugin.placeholder, language="en")
        source_placeholder = plugin.placeholder
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertTrue(
                target_placeholder
                .get_plugins(translation.language)
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_cant_copy_plugin(self):
        """
        User can't copy a plugin if he
        does not have change permissions on the Page model,
        does not have add permissions on the plugin model,
        and/or does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugin = self._add_plugin_to_page(page)
        translation = self._add_translation_to_page(page)
        endpoint = self.get_copy_plugin_uri(plugin, container=plugin.placeholder, language="en")
        source_placeholder = plugin.placeholder
        target_placeholder = page.get_placeholders('en').get(slot='right-column')

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': translation.language,
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertFalse(
                target_placeholder
                .get_plugins(translation.language)
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    # Placeholder related tests

    def test_user_can_clear_empty_placeholder(self):
        """
        User can clear an empty placeholder if he has change permissions
        on the Page model and global change permissions.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder, container=placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)

    # def test_user_cant_clear_empty_placeholder(self):
    #     """
    #     User can't clear an empty placeholder if he does not have
    #     change permissions on the Page model and/or does not have
    #     global change permissions.
    #     """
    #     page = self.get_permissions_test_page()
    #
    #     staff_user = self.get_staff_user_with_no_permissions()
    #     placeholder = page.get_placeholders("en").get(slot='body')
    #     endpoint = self.get_clear_placeholder_url(placeholder)
    #
    #     self.add_permission(staff_user, 'change_page')
    #     self.add_global_permission(staff_user, can_change=False)
    #
    #     with self.login_user_context(staff_user):
    #         response = self.client.post(endpoint, {'test': 0})
    #         self.assertEqual(response.status_code, 403)
    #
    # def test_user_can_clear_non_empty_placeholder(self):
    #     """
    #     User can clear a placeholder with plugins if he has
    #     change permissions on the Page model, delete permissions
    #     on the plugin models in the placeholder and global change permissions.
    #     """
    #     page = self.get_permissions_test_page()
    #     staff_user = self.get_staff_user_with_no_permissions()
    #     plugins = [
    #         self._add_plugin_to_page(page, 'TextPlugin'),
    #         self._add_plugin_to_page(page, 'LinkPlugin'),
    #     ]
    #     placeholder = plugins[0].placeholder
    #     endpoint = self.get_clear_placeholder_url(placeholder)
    #
    #     self.add_permission(staff_user, 'delete_text')
    #     self.add_permission(staff_user, 'delete_link')
    #     self.add_permission(staff_user, 'change_page')
    #     self.add_global_permission(staff_user, can_change=True)
    #
    #     with self.login_user_context(staff_user):
    #         response = self.client.post(endpoint, {'test': 0})
    #         self.assertEqual(response.status_code, 302)
    #         self.assertEqual(placeholder.get_plugins('en').count(), 0)
    #
    # def test_user_cant_clear_non_empty_placeholder(self):
    #     """
    #     User can't clear a placeholder with plugins if he does not have
    #     change permissions on the Page model, does not have delete
    #     permissions on the plugin models in the placeholder and/or
    #     does not have global change permissions.
    #     """
    #     page = self.get_permissions_test_page()
    #     staff_user = self.get_staff_user_with_no_permissions()
    #     plugins = [
    #         self._add_plugin_to_page(page, 'TextPlugin'),
    #         self._add_plugin_to_page(page, 'LinkPlugin'),
    #     ]
    #     placeholder = plugins[0].placeholder
    #     endpoint = self.get_clear_placeholder_url(placeholder)
    #
    #     self.add_permission(staff_user, 'delete_text')
    #     self.add_permission(staff_user, 'delete_link')
    #     self.add_permission(staff_user, 'change_page')
    #     self.add_global_permission(staff_user, can_change=False)
    #
    #     with self.login_user_context(staff_user):
    #         response = self.client.post(endpoint, {'test': 0})
    #         self.assertEqual(response.status_code, 403)
    #         self.assertEqual(placeholder.get_plugins('en').count(), 2)
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    # def test_copy_plugins_add_plugins_from_placeholder(self):
    #     """
    #     Test that the Placeholder admin copy_plugins endpoint
    #     using the option to add plugins from a created placeholder
    #     """
    #     superuser = self.get_superuser()
    #     source_placeholder = Placeholder.objects.create(slot='source')
    #     target_placeholder = Placeholder.objects.create(slot='target')
    #     add_plugin(
    #         source_placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #     endpoint = self.get_admin_url(Placeholder, 'copy_plugins')
    #
    #     with self.login_user_context(superuser):
    #         data = {
    #             'source_language': "en",
    #             'source_placeholder_id': source_placeholder.pk,
    #             'target_language': "en",
    #             'target_placeholder_id': target_placeholder.pk,
    #         }
    #         response = self.client.post(endpoint, data)
    #         self.assertEqual(response.status_code, 200)
    #
    # def test_copy_plugins_copy_plugin_to_clipboard(self):
    #     """
    #     Test that the Placeholder admin copy_plugins endpoint
    #     using the option to copy a plugin to the clipboard
    #     """
    #     superuser = self.get_superuser()
    #     user_settings = UserSettings.objects.create(
    #         language="en",
    #         user=superuser,
    #         clipboard=Placeholder.objects.create(),
    #     )
    #     source_placeholder = Placeholder.objects.create(slot='source')
    #     source_plugin = add_plugin(
    #         source_placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #     endpoint = self.get_admin_url(Placeholder, 'copy_plugins')
    #
    #     with self.login_user_context(superuser):
    #         data = {
    #             'source_language': "en",
    #             'source_placeholder_id': source_placeholder.pk,
    #             'source_plugin_id': source_plugin.pk,
    #             'target_language': "en",
    #             'target_placeholder_id': user_settings.clipboard.pk,
    #         }
    #         response = self.client.post(endpoint, data)
    #         self.assertEqual(response.status_code, 200)
    #
    # def test_copy_plugins_copy_placeholder_to_clipboard(self):
    #     """
    #     Test that the Placeholder admin copy_plugins endpoint
    #     using the option to copy the placeholder to the clipboard
    #     """
    #     superuser = self.get_superuser()
    #     user_settings = UserSettings.objects.create(
    #         language="en",
    #         user=superuser,
    #         clipboard=Placeholder.objects.create(),
    #     )
    #
    #     source_placeholder = Placeholder.objects.create(slot='source')
    #     add_plugin(
    #         source_placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #     endpoint = self.get_admin_url(Placeholder, 'copy_plugins')
    #
    #     with self.login_user_context(superuser):
    #         data = {
    #             'source_language': "en",
    #             'source_placeholder_id': source_placeholder.pk,
    #             'target_language': "en",
    #             'target_placeholder_id': user_settings.clipboard.pk,
    #         }
    #         response = self.client.post(endpoint, data)
    #         self.assertEqual(response.status_code, 200)
    #
    # def test_edit_plugin_endpoint(self):
    #     """
    #     Test that the Placeholder admin edit_plugins endpoint works
    #     """
    #     superuser = self.get_superuser()
    #     placeholder = Placeholder.objects.create(slot='edit_plugin_placeholder')
    #     plugin = add_plugin(
    #         placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #     endpoint = self.get_admin_url(Placeholder, 'edit_plugin', plugin.pk)
    #
    #     with self.login_user_context(superuser):
    #         data = model_to_dict(plugin, fields=['plugin_type', 'language', 'body'])
    #         data['body'] = 'Contents modified'
    #         response = self.client.post(endpoint, data)
    #         self.assertEqual(response.status_code, 200)
    #
    # def test_move_plugin_endpoint(self):
    #     """
    #     Test that the Placeholder admin move_plugin endpoint works
    #
    #     TODO: Test
    #         - _paste_placeholder
    #         - _paste_plugin
    #         - _cut_plugin
    #         - _move_plugin
    #     """
    #     superuser = self.get_superuser()
    #     source_placeholder = Placeholder.objects.create(slot='source')
    #     target_placeholder = Placeholder.objects.create(slot='target')
    #     plugin = add_plugin(
    #         source_placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #
    #     endpoint = self.get_admin_url(Placeholder, 'move_plugin')
    #
    #     with self.login_user_context(superuser):
    #         data = {
    #             'plugin_id': plugin.pk,
    #             'target_language': 'en',
    #             'placeholder_id': target_placeholder.pk,
    #             'target_position': 1,
    #         }
    #         response = self.client.post(endpoint, data)
    #         self.assertEqual(response.status_code, 200)
    #
    # def test_delete_plugin_endpoint(self):
    #     """
    #     Test that the Placeholder admin delete_plugin endpoint works
    #     """
    #     superuser = self.get_superuser()
    #     placeholder = Placeholder.objects.create(slot='source')
    #     plugin = add_plugin(
    #         placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #     endpoint = self.get_admin_url(Placeholder, 'delete_plugin', plugin.pk)
    #
    #     with self.login_user_context(superuser):
    #         data = {'post': True}
    #         response = self.client.post(endpoint, data)
    #         self.assertEqual(response.status_code, 302)
    #
    # def test_clear_placeholder_endpoint(self):
    #     """
    #     Test that the Placeholder admin delete_plugin endpoint works
    #     """
    #     superuser = self.get_superuser()
    #     placeholder = Placeholder.objects.create(slot='source')
    #     add_plugin(
    #         placeholder,
    #         plugin_type="TextPlugin",
    #         language="en",
    #         body="Contents of the text plugin",
    #     )
    #     endpoint = self.get_admin_url(Placeholder, 'clear_placeholder', placeholder.pk)
    #
    #     with self.login_user_context(superuser):
    #         response = self.client.get(endpoint)
    #         self.assertEqual(response.status_code, 200)
