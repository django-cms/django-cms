# -*- coding: utf-8 -*-
from django.forms.models import model_to_dict
from django.test.utils import override_settings

from cms.api import add_plugin
from cms.models import CMSPlugin, Placeholder, UserSettings
from cms.test_utils.project.placeholderapp.models import Example1
from cms.test_utils.testcases import CMSTestCase


class AppAdminTestCase(CMSTestCase):

    def setUp(self):
        self._obj = self._get_example_obj()

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

    def _get_add_plugin_uri(self, plugin_type='LinkPlugin', language='en'):
        uri = self.get_add_plugin_uri(
            placeholder=self._obj.placeholder,
            plugin_type=plugin_type,
            language=language,
        )
        return uri

    def _get_example_obj(self):
        obj = Example1.objects.create(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        return obj


class AppAdminTest(AppAdminTestCase):
    placeholderconf = {'placeholder': {
        'limits': {
            'global': 2,
            'StylePlugin': 1,
        }
    }
    }

    def test_global_limit_on_plugin_add(self):
        """
        Ensures placeholder global plugin limit is respected
        when adding plugins to the placeholder.
        """
        superuser = self.get_superuser()
        endpoint = self._get_add_plugin_uri()

        with self.login_user_context(superuser):
            with override_settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 200)
                response = self.client.post(endpoint, data)  # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.content,
                    b"This placeholder already has the maximum number of plugins (2).",
                )

    def test_global_limit_on_plugin_move(self):
        """
        Ensures placeholder global plugin limit is respected
        when moving plugins to the placeholder.
        """
        superuser = self.get_superuser()
        source_placeholder = self._obj.placeholder
        target_placeholder = self._get_example_obj().placeholder

        plugin_1 = self._add_plugin_to_placeholder(source_placeholder)
        plugin_2 = self._add_plugin_to_placeholder(source_placeholder)
        plugin_3 = self._add_plugin_to_placeholder(source_placeholder)

        with self.login_user_context(superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = {
                    'plugin_id': plugin_1.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                }
                endpoint = self.get_move_plugin_uri(plugin_1, container=Example1)
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                data = {
                    'plugin_id': plugin_2.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                }
                endpoint = self.get_move_plugin_uri(plugin_2, container=Example1)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 200)
                data = {
                    'plugin_id': plugin_3.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                }
                endpoint = self.get_move_plugin_uri(plugin_3, container=Example1)
                response = self.client.post(endpoint, data)  # third
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.content,
                    b"This placeholder already has the maximum number of plugins (2)."
                )

    def test_no_global_limit_check_same_placeholder_move(self):
        """
        Ensures no global limit exception is raised
        when moving plugins inside of a placeholder.
        """
        superuser = self.get_superuser()
        source_placeholder = self._obj.placeholder
        target_placeholder = source_placeholder

        plugin_1 = self._add_plugin_to_placeholder(source_placeholder)
        plugin_2 = self._add_plugin_to_placeholder(source_placeholder)

        with self.login_user_context(superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = {
                    'plugin_id': plugin_1.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                    'plugin_order': 1,
                }
                endpoint = self.get_move_plugin_uri(plugin_1, container=Example1)
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                data = {
                    'plugin_id': plugin_2.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                    'plugin_order': 1,
                }
                endpoint = self.get_move_plugin_uri(plugin_2, container=Example1)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 200)

    def test_type_limit_on_plugin_add(self):
        """
        Ensures placeholder plugin type limit is respected
        when adding plugins to the placeholder.
        """
        superuser = self.get_superuser()
        endpoint = self._get_add_plugin_uri('StylePlugin')

        with self.login_user_context(superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = {'tag_type': 'div'}
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.content,
                    b"This placeholder already has the "
                    b"maximum number (1) of allowed Style plugins."
                )

    def test_type_limit_on_plugin_move(self):
        """
        Ensures placeholder plugin type limit is respected
        when moving plugins to the placeholder.
        """
        superuser = self.get_superuser()
        source_placeholder = self._obj.placeholder
        target_placeholder = self._get_example_obj().placeholder

        plugin_1 = self._add_plugin_to_placeholder(source_placeholder, 'StylePlugin')
        plugin_2 = self._add_plugin_to_placeholder(source_placeholder, 'StylePlugin')

        with self.login_user_context(superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = {
                    'plugin_id': plugin_1.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                }
                endpoint = self.get_move_plugin_uri(plugin_1, container=Example1)
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)
                data = {
                    'plugin_id': plugin_2.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                }
                endpoint = self.get_move_plugin_uri(plugin_2, container=Example1)
                response = self.client.post(endpoint, data)  # second
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content,
                                 b"This placeholder already has the maximum number (1) of allowed Style plugins.")

    def test_no_type_limit_check_same_placeholder_move(self):
        """
        Ensures no plugin type limit exception is raised
        when moving plugins inside of a placeholder.
        """
        superuser = self.get_superuser()
        source_placeholder = self._obj.placeholder
        target_placeholder = source_placeholder

        plugin_1 = self._add_plugin_to_placeholder(source_placeholder, 'StylePlugin')

        with self.login_user_context(superuser):
            with self.settings(CMS_PLACEHOLDER_CONF=self.placeholderconf):
                data = {
                    'plugin_id': plugin_1.pk,
                    'placeholder_id': target_placeholder.pk,
                    'target_language': 'en',
                    'plugin_parent': '',
                    'plugin_order': 1,
                }
                endpoint = self.get_move_plugin_uri(plugin_1, container=Example1)
                response = self.client.post(endpoint, data)  # first
                self.assertEqual(response.status_code, 200)


class AppAdminPermissionsTest(AppAdminTestCase):

    def setUp(self):
        self._obj = self._get_example_obj()
        self._staff_user = self.get_staff_user_with_no_permissions()

    def test_user_can_add_plugin(self):
        """
        User can add a new plugin if he has change permissions
        on the model attached to the placeholder and he has
        add permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri()

        self.add_permission(staff_user, 'change_example1')
        self.add_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(plugins.count(), 1)

    def test_user_cant_add_plugin(self):
        """
        User can't add a new plugin if he does not have
        change permissions on the model attached to the placeholder
        and/or does not have add permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugins = placeholder.get_plugins('en').filter(plugin_type='LinkPlugin')
        endpoint = self._get_add_plugin_uri()

        self.add_permission(staff_user, 'add_example1')
        self.add_permission(staff_user, 'delete_example1')
        self.add_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(plugins.count(), 0)

        self.add_permission(staff_user, 'change_example1')
        self.remove_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(plugins.count(), 0)

    def test_user_can_edit_plugin(self):
        """
        User can edit a plugin if he has change permissions
        on the model attached to the placeholder and he has
        change permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_change_plugin_uri(plugin, container=Example1)

        self.add_permission(staff_user, 'change_example1')
        self.add_permission(staff_user, 'change_link')

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'external_link'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            plugin.refresh_from_db()
            self.assertEqual(plugin.name, data['name'])

    def test_user_cant_edit_plugin(self):
        """
        User can't edit a plugin if he does not have
        change permissions on the model attached to the placeholder
        and/or does not have change permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_change_plugin_uri(plugin, container=Example1)

        self.add_permission(staff_user, 'add_example1')
        self.add_permission(staff_user, 'delete_example1')
        self.add_permission(staff_user, 'change_link')

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'external_link'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            plugin.refresh_from_db()
            self.assertNotEqual(plugin.name, data['name'])

        self.add_permission(staff_user, 'change_example1')
        self.remove_permission(staff_user, 'change_link')

        with self.login_user_context(staff_user):
            data = model_to_dict(plugin, fields=['name', 'external_link'])
            data['name'] = 'A link 2'

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            plugin.refresh_from_db()
            self.assertNotEqual(plugin.name, data['name'])

    def test_user_can_delete_plugin(self):
        """
        User can delete a plugin if he has change permissions
        on the model attached to the placeholder and he has
        delete permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_delete_plugin_uri(plugin, container=Example1)

        self.add_permission(staff_user, 'change_example1')
        self.add_permission(staff_user, 'delete_link')

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 302)
            self.assertFalse(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_cant_delete_plugin(self):
        """
        User can't delete a plugin if he does not have
        change permissions on the model attached to the placeholder
        and/or does not have delete permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_delete_plugin_uri(plugin, container=Example1)

        self.add_permission(staff_user, 'add_example1')
        self.add_permission(staff_user, 'delete_example1')
        self.add_permission(staff_user, 'delete_link')

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

        self.add_permission(staff_user, 'change_example1')
        self.remove_permission(staff_user, 'delete_link')

        with self.login_user_context(staff_user):
            data = {'post': True}

            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(CMSPlugin.objects.filter(pk=plugin.pk).exists())

    def test_user_can_move_plugin(self):
        """
        User can move a plugin if he has change permissions
        on the model attached to the placeholder and he has
        change permissions on the plugin model.
        """
        staff_user = self._staff_user
        source_placeholder = self._obj.placeholder
        target_placeholder = self._get_example_obj().placeholder
        plugin = self._add_plugin_to_placeholder(source_placeholder)

        data = {
            'plugin_id': plugin.pk,
            'target_language': 'en',
            'placeholder_id': target_placeholder.pk,
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'change_example1')
        self.add_permission(staff_user, 'change_link')

        with self.login_user_context(staff_user):
            endpoint = self.get_move_plugin_uri(plugin, container=Example1)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertFalse(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_cant_move_plugin(self):
        """
        User can't move a plugin if he does not have
        change permissions on the model attached to the placeholder
        and/or does not have change permissions on the plugin model.
        """
        staff_user = self._staff_user
        source_placeholder = self._obj.placeholder
        target_placeholder = self._get_example_obj().placeholder
        plugin = self._add_plugin_to_placeholder(source_placeholder)

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': target_placeholder.pk,
            'target_language': 'en',
            'plugin_parent': '',
        }

        self.add_permission(staff_user, 'add_example1')
        self.add_permission(staff_user, 'delete_example1')
        self.add_permission(staff_user, 'change_link')

        with self.login_user_context(staff_user):
            endpoint = self.get_move_plugin_uri(plugin, container=Example1)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

        self.add_permission(staff_user, 'change_example1')
        self.remove_permission(staff_user, 'change_link')

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(target_placeholder.get_plugins('en').filter(pk=plugin.pk))
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk))

    def test_user_can_copy_plugin(self):
        """
        User can copy a plugin if he has change permissions
        on the model attached to the placeholder and he has
        add permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_copy_plugin_uri(plugin, container=Example1)
        source_placeholder = plugin.placeholder
        target_placeholder = self._get_example_obj().placeholder

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': 'en',
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'change_example1')
        self.add_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertTrue(
                target_placeholder
                .get_plugins('en')
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_cant_copy_plugin(self):
        """
        User can't copy a plugin if he does not have
        change permissions on the model attached to the placeholder
        and/or does not have add permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugin = self._add_plugin_to_placeholder(placeholder)
        endpoint = self.get_copy_plugin_uri(plugin, container=Example1)
        source_placeholder = plugin.placeholder
        target_placeholder = self._get_example_obj().placeholder

        data = {
            'source_plugin_id': plugin.pk,
            'source_placeholder_id': source_placeholder.pk,
            'source_language': plugin.language,
            'target_language': 'en',
            'target_placeholder_id': target_placeholder.pk,
        }

        self.add_permission(staff_user, 'add_example1')
        self.add_permission(staff_user, 'delete_example1')
        self.add_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertFalse(
                target_placeholder
                .get_plugins('en')
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

        self.add_permission(staff_user, 'change_example1')
        self.remove_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(source_placeholder.get_plugins('en').filter(pk=plugin.pk).exists())
            self.assertFalse(
                target_placeholder
                .get_plugins('en')
                .filter(plugin_type=plugin.plugin_type)
                .exists()
            )

    def test_user_can_clear_empty_placeholder(self):
        """
        User can clear a placeholder if he has change permissions
        on the model attached to the placeholder.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        endpoint = self.get_clear_placeholder_url(placeholder, container=Example1)

        self.add_permission(staff_user, 'change_example1')

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)

    def test_user_cant_clear_empty_placeholder(self):
        """
        User can't clear a placeholder if he does not have
        change permissions on the model attached to the placeholder.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        endpoint = self.get_clear_placeholder_url(placeholder, container=Example1)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 403)

    def test_user_can_clear_non_empty_placeholder(self):
        """
        User can clear a placeholder with plugins if he has
        change permissions on the model attached to the placeholder
        and delete permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugins = [
            self._add_plugin_to_placeholder(placeholder, 'StylePlugin'),
            self._add_plugin_to_placeholder(placeholder, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder, container=Example1)

        self.add_permission(staff_user, 'delete_style')
        self.add_permission(staff_user, 'delete_link')
        self.add_permission(staff_user, 'change_example1')

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'test': 0})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(placeholder.get_plugins('en').count(), 0)

    def test_user_cant_clear_non_empty_placeholder(self):
        """
        User can't clear a placeholder with plugins if he does not have
        change permissions on the model attached to the placeholder
        and/or does not have delete permissions on the plugin model.
        """
        staff_user = self._staff_user
        placeholder = self._obj.placeholder
        plugins = [
            self._add_plugin_to_placeholder(placeholder, 'StylePlugin'),
            self._add_plugin_to_placeholder(placeholder, 'LinkPlugin'),
        ]
        placeholder = plugins[0].placeholder
        endpoint = self.get_clear_placeholder_url(placeholder, container=Example1)

        self.add_permission(staff_user, 'delete_text')
        self.add_permission(staff_user, 'delete_link')

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
        staff_user = self._staff_user
        source_placeholder = self._obj.placeholder
        endpoint = self.get_copy_placeholder_uri(source_placeholder, container=Example1)

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
        staff_user = self._staff_user
        source_placeholder = self._obj.placeholder
        endpoint = self.get_copy_placeholder_uri(source_placeholder, container=Example1)

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
        staff_user = self._staff_user
        target_placeholder = self._obj.placeholder

        self.add_permission(staff_user, 'change_example1')
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
                'plugin_order[]': '__COPY__',
                'move_a_copy': True,
            }
            endpoint = self.get_move_plugin_uri(placeholder_plugin, container=Example1)
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
        staff_user = self._staff_user
        target_placeholder = self._obj.placeholder

        self.add_permission(staff_user, 'add_example1')
        self.add_permission(staff_user, 'delete_example1')
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
                'plugin_order[]': '__COPY__',
                'move_a_copy': True,
            }
            endpoint = self.get_move_plugin_uri(placeholder_plugin, container=Example1)
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(target_placeholder.get_plugins('fr').count(), 0)

        self.add_permission(staff_user, 'change_example1')
        self.remove_permission(staff_user, 'add_link')

        with self.login_user_context(staff_user):
            # Paste plugins from clipboard into placeholder
            # under the french language.
            data = {
                'placeholder_id': target_placeholder.pk,
                'plugin_id': placeholder_plugin.pk,
                'plugin_parent': '',
                'target_language': 'fr',
                'plugin_order[]': '__COPY__',
                'move_a_copy': True,
            }
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(target_placeholder.get_plugins('fr').count(), 0)
