# -*- coding: utf-8 -*-
from django.forms.models import model_to_dict
from django.utils.http import urlencode

from cms.api import add_plugin, create_page, create_title
from cms.models import Placeholder, UserSettings, CMSPlugin
from cms.test_utils.testcases import CMSTestCase


class PlaceholderAdminTestCase(CMSTestCase):

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


class PlaceholderAdminPermissionsTestCase(CMSTestCase):

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

    def _add_plugin_to_placeholder(self, placeholder,
                                   plugin_type='LinkPlugin', language='en'):
        plugin_data = {
            'StylePlugin': {'tag_type': 'div'},
            'LinkPlugin': {'name': 'A Link', 'external_link': 'https://www.django-cms.org'},
            'PlaceholderPlugin': {'name': 'Content'},
        }
        plugin = add_plugin(
            placeholder,
            plugin_type,
            language,
            **plugin_data[plugin_type]
        )
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

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_text')
        self.add_global_permission(staff_user, can_change=True)

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
        self.add_permission(staff_user, 'change_page')
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
        plugin = self._add_plugin_to_page(page, language="en")
        endpoint = self.get_change_plugin_uri(plugin, container=Placeholder, language="en")

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
        endpoint = self.get_move_plugin_uri(plugin, container=Placeholder, language="en")
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
        endpoint = self.get_move_plugin_uri(plugin, container=Placeholder, language="en")
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
        endpoint = self.get_copy_plugin_uri(plugin, container=Placeholder, language="en")
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
        endpoint = self.get_copy_plugin_uri(plugin, container=Placeholder, language="en")
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

    def test_user_can_clear_empty_placeholder(self):
        """
        User can clear an empty placeholder if he has change permissions
        on the Page model and global change permissions.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        placeholder = page.get_placeholders("en").get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder, container=Placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)

    def test_user_cant_clear_empty_placeholder(self):
        """
        User can't clear an empty placeholder if he does not have
        change permissions on the Page model and/or does not have
        global change permissions.
        """
        page = self.get_permissions_test_page()

        staff_user = self.get_staff_user_with_no_permissions()
        placeholder = page.get_placeholders("en").get(slot='body')
        endpoint = self.get_clear_placeholder_url(placeholder, container=Placeholder, language="en")

        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)

    def test_user_can_clear_non_empty_placeholder(self):
        """
        User can clear a placeholder with plugins if he has
        change permissions on the Page model, delete permissions
        on the plugin models in the placeholder and global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder, container=Placeholder, language="en")

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)

    def test_user_cant_clear_non_empty_placeholder(self):
        """
        User can't clear a placeholder with plugins if he does not have
        change permissions on the Page model, does not have delete
        permissions on the plugin models in the placeholder and/or
        does not have global change permissions.
        """
        page = self.get_permissions_test_page()
        staff_user = self.get_staff_user_with_no_permissions()
        plugins = [
            self._add_plugin_to_page(page, 'TextPlugin'),
            self._add_plugin_to_page(page, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder, container=Placeholder, language="en")

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_page')
        self.add_global_permission(staff_user, can_change=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(placeholder.get_plugins('en').count(), 2)

    def test_user_can_copy_placeholder_to_clipboard(self):
        """
        User can copy a placeholder to the clipboard
        if he has add permissions on the plugin models
        being copied.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        source_placeholder = page.get_placeholders('en').get(slot='right-column')
        endpoint = self.get_copy_placeholder_uri(source_placeholder, container=Placeholder, language="en")

        self._add_plugin_to_placeholder(source_placeholder, 'StylePlugin')
        self._add_plugin_to_placeholder(source_placeholder, 'LinkPlugin')

        user_settings = UserSettings.objects.create(
            language="en",
            user=staff_user,
            clipboard=Placeholder.objects.create(),
        )

        self.add_permission(staff_user, 'add_link')
        self.add_permission(staff_user, 'add_style')

        data = {
            'source_plugin_id': '',
            'source_placeholder_id': source_placeholder.pk,
            'source_language': 'en',
            'target_language': 'en',
            'target_placeholder_id': user_settings.clipboard.pk,
        }

        with self.login_user_context(staff_user):
            # Copy plugins into the clipboard
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)

        clipboard_plugins = user_settings.clipboard.get_plugins()

        # assert the clipboard has a PlaceholderPlugin
        self.assertTrue(clipboard_plugins.filter(plugin_type='PlaceholderPlugin').exists())
        self.assertEqual(len(clipboard_plugins), 1)

        placeholder_plugin = clipboard_plugins[0].get_plugin_instance()[0]
        ref_placeholder = placeholder_plugin.placeholder_ref

        # assert there's only two plugins in the clipboard
        self.assertEqual(ref_placeholder.get_plugins().count(), 2)

    def test_user_cant_copy_placeholder_to_clipboard(self):
        """
        User cant copy a placeholder to the clipboard if he does not
        have add permissions on the plugin models being copied.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        source_placeholder = page.get_placeholders("en").get(slot='body')
        endpoint = self.get_copy_placeholder_uri(source_placeholder, container=Placeholder, language="en")

        self._add_plugin_to_placeholder(source_placeholder, 'StylePlugin')
        self._add_plugin_to_placeholder(source_placeholder, 'LinkPlugin')

        user_settings = UserSettings.objects.create(
            language="en",
            user=staff_user,
            clipboard=Placeholder.objects.create(),
        )

        self.add_permission(staff_user, 'change_link')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_style')
        self.add_permission(staff_user, 'delete_style')

        data = {
            'source_plugin_id': '',
            'source_placeholder_id': source_placeholder.pk,
            'source_language': 'en',
            'target_language': 'en',
            'target_placeholder_id': user_settings.clipboard.pk,
        }

        with self.login_user_context(staff_user):
            # Copy plugins into the clipboard
            response = self.client.post(endpoint, data)

        self.assertEqual(response.status_code, 403)
        clipboard_plugins = user_settings.clipboard.get_plugins()
        self.assertEqual(len(clipboard_plugins), 0)

    def test_user_can_paste_from_clipboard(self):
        """
        User can paste plugins from the clipboard if he has
        change permissions on the model attached to the target
        placeholder and he has add permissions on the plugin models
        being copied.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        target_placeholder = page.get_placeholders("en").get(slot='body')

        self.add_permission(staff_user, 'change_page')
        self.add_permission(staff_user, 'add_link')
        self.add_global_permission(staff_user, can_change=True)

        user_settings = UserSettings.objects.create(
            language="en",
            user=staff_user,
            clipboard=Placeholder.objects.create(),
        )

        placeholder_plugin = self._add_plugin_to_placeholder(
            user_settings.clipboard,
            'PlaceholderPlugin',
        )
        ref_placeholder = placeholder_plugin.placeholder_ref

        self._add_plugin_to_placeholder(ref_placeholder)
        self._add_plugin_to_placeholder(ref_placeholder)

        with self.login_user_context(staff_user):
            # Paste plugins from clipboard into placeholder
            # under the french language.
            data = {
                'placeholder_id': target_placeholder.pk,
                'plugin_id': placeholder_plugin.pk,
                'plugin_parent': '',
                'target_language': 'fr',
                'move_a_copy': True,
                'target_position': target_placeholder.get_next_plugin_position('fr', insert_order='last'),
            }
            endpoint = self.get_move_plugin_uri(placeholder_plugin, container=Placeholder)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(target_placeholder.get_plugins('fr').count(), 2)

    def test_user_cant_paste_from_clipboard(self):
        """
        User cant paste plugins from the clipboard if he does not have
        change permissions on the model attached to the target placeholder
        and/or does not have add permissions on the plugin models
        being copied.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        page = self.get_permissions_test_page()
        target_placeholder = page.get_placeholders("en").get(slot='body')

        self.add_permission(staff_user, 'add_placeholder')
        self.add_permission(staff_user, 'delete_placeholder')
        self.add_permission(staff_user, 'add_link')

        user_settings = UserSettings.objects.create(
            language="en",
            user=staff_user,
            clipboard=Placeholder.objects.create(),
        )

        placeholder_plugin = self._add_plugin_to_placeholder(
            user_settings.clipboard,
            'PlaceholderPlugin',
        )
        ref_placeholder = placeholder_plugin.placeholder_ref

        self._add_plugin_to_placeholder(ref_placeholder)
        self._add_plugin_to_placeholder(ref_placeholder)

        with self.login_user_context(staff_user):
            # Paste plugins from clipboard into placeholder
            # under the french language.
            data = {
                'placeholder_id': target_placeholder.pk,
                'plugin_id': placeholder_plugin.pk,
                'plugin_parent': '',
                'target_language': 'fr',
                'move_a_copy': True,
                'target_position': target_placeholder.get_next_plugin_position('fr', insert_order='last'),
            }
            endpoint = self.get_move_plugin_uri(placeholder_plugin, container=Placeholder)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(target_placeholder.get_plugins('fr').count(), 0)

        self.add_permission(staff_user, 'change_placeholder')
        self.remove_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            # Paste plugins from clipboard into placeholder
            # under the french language.
            data = {
                'placeholder_id': target_placeholder.pk,
                'plugin_id': placeholder_plugin.pk,
                'plugin_parent': '',
                'target_language': 'fr',
                'move_a_copy': True,
                'target_position': target_placeholder.get_next_plugin_position('fr', insert_order='last'),
            }
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(target_placeholder.get_plugins('fr').count(), 0)