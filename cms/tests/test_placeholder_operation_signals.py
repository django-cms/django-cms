from cms.api import add_plugin
from cms.models import Placeholder, UserSettings
from cms.operations import (
    ADD_PLUGIN,
    ADD_PLUGINS_FROM_PLACEHOLDER,
    CHANGE_PLUGIN,
    CLEAR_PLACEHOLDER,
    CUT_PLUGIN,
    DELETE_PLUGIN,
    MOVE_PLUGIN,
    PASTE_PLACEHOLDER,
    PASTE_PLUGIN,
)
from cms.signals import post_placeholder_operation, pre_placeholder_operation
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import signal_tester


class PagePlaceholderTestCase(CMSTestCase):

    def _add_plugin(self, placeholder=None, plugin_type='LinkPlugin', language='en'):
        placeholder = placeholder or self._placeholder_1
        plugin_data = {
            'LinkPlugin': {'name': 'A Link', 'external_link': 'https://www.django-cms.org'},
            'PlaceholderPlugin': {},
        }
        plugin = add_plugin(
            placeholder,
            plugin_type,
            language,
            **plugin_data[plugin_type]
        )
        return plugin

    def _get_add_plugin_uri(self, language='en'):
        uri = self.get_add_plugin_uri(
            placeholder=self._placeholder_1,
            plugin_type='LinkPlugin',
            language=language,
        )
        return uri

    def setUp(self):
        self._admin_user = self.get_superuser()
        self._cms_page = self.create_homepage(
            "home",
            "nav_playground.html",
            "en",
            created_by=self._admin_user,
        )
        self._placeholder_1 = self._cms_page.get_placeholders("en").get(slot='body')
        self._placeholder_2 = self._cms_page.get_placeholders("en").get(slot='right-column')

    def test_pre_add_plugin(self):
        with signal_tester(pre_placeholder_operation) as env:
            endpoint = self._get_add_plugin_uri()
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}

            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            self.assertEqual(call_kwargs['operation'], ADD_PLUGIN)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(call_kwargs['placeholder'], self._placeholder_1)
            self.assertEqual(call_kwargs['plugin'].name, data['name'])
            self.assertEqual(call_kwargs['plugin'].external_link, data['external_link'])

    def test_post_add_plugin(self):
        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            endpoint = self._get_add_plugin_uri()
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}

            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], ADD_PLUGIN)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(post_call_kwargs['placeholder'], self._placeholder_1)
            self.assertTrue(post_call_kwargs['plugin'].pk)
            self.assertEqual(post_call_kwargs['plugin'].name, data['name'])
            self.assertEqual(post_call_kwargs['plugin'].external_link, data['external_link'])

    def test_pre_edit_plugin(self):
        plugin = self._add_plugin()
        endpoint = self.get_change_plugin_uri(plugin)

        with signal_tester(pre_placeholder_operation) as env:
            data = {'name': 'A Link 2', 'external_link': 'https://www.django-cms.org'}

            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            self.assertEqual(call_kwargs['operation'], CHANGE_PLUGIN)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(call_kwargs['placeholder'], self._placeholder_1)
            self.assertEqual(call_kwargs['old_plugin'].name, 'A Link')
            self.assertEqual(call_kwargs['old_plugin'].external_link, data['external_link'])
            self.assertEqual(call_kwargs['new_plugin'].name, data['name'])
            self.assertEqual(call_kwargs['new_plugin'].external_link, data['external_link'])

    def test_post_edit_plugin(self):
        plugin = self._add_plugin()
        endpoint = self.get_change_plugin_uri(plugin)

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            data = {'name': 'A Link 2', 'external_link': 'https://www.django-cms.org'}

            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], CHANGE_PLUGIN)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(post_call_kwargs['placeholder'], self._placeholder_1)
            self.assertEqual(post_call_kwargs['old_plugin'].name, 'A Link')
            self.assertEqual(post_call_kwargs['old_plugin'].external_link, data['external_link'])
            self.assertEqual(post_call_kwargs['new_plugin'].name, data['name'])
            self.assertEqual(post_call_kwargs['new_plugin'].external_link, data['external_link'])

    def test_pre_delete_plugin(self):
        plugin = self._add_plugin()
        endpoint = self.get_delete_plugin_uri(plugin)

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                data = {'post': True}

                response = self.client.post(endpoint, data)
                self.assertContains(response, '<div class="success"></div>')

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            self.assertEqual(call_kwargs['operation'], DELETE_PLUGIN)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(call_kwargs['placeholder'], self._placeholder_1)
            self.assertEqual(call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(call_kwargs['plugin'].external_link, 'https://www.django-cms.org')

    def test_post_delete_plugin(self):
        plugin = self._add_plugin()
        endpoint = self.get_delete_plugin_uri(plugin)

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                data = {'post': True}

                response = self.client.post(endpoint, data)
                self.assertContains(response, '<div class="success"></div>')

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], DELETE_PLUGIN)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(post_call_kwargs['placeholder'], self._placeholder_1)
            self.assertEqual(post_call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(post_call_kwargs['plugin'].external_link, 'https://www.django-cms.org')

    def test_pre_move_plugin(self):
        plugin = self._add_plugin()
        endpoint = self.get_move_plugin_uri(plugin)
        source_placeholder = plugin.placeholder

        data = {
            'plugin_id': plugin.pk,
            'target_language': 'en',
            'placeholder_id': self._placeholder_2.pk,
            'target_position': 1,
        }

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            self.assertEqual(call_kwargs['operation'], MOVE_PLUGIN)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(call_kwargs['plugin'].placeholder, source_placeholder)
            self.assertEqual(call_kwargs['plugin'].external_link, 'https://www.django-cms.org')
            self.assertEqual(call_kwargs['source_language'], 'en')
            self.assertEqual(call_kwargs['source_placeholder'], source_placeholder)
            self.assertEqual(call_kwargs['source_parent_id'], plugin.parent_id)
            self.assertEqual(call_kwargs['target_language'], 'en')
            self.assertEqual(call_kwargs['target_placeholder'], self._placeholder_2)
            self.assertEqual(call_kwargs['target_parent_id'], None)

    def test_post_move_plugin(self):
        plugin = self._add_plugin()
        endpoint = self.get_move_plugin_uri(plugin)
        source_placeholder = plugin.placeholder

        data = {
            'plugin_id': plugin.pk,
            'target_language': 'en',
            'placeholder_id': self._placeholder_2.pk,
            'target_position': 1,
        }

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], MOVE_PLUGIN)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(post_call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(post_call_kwargs['plugin'].placeholder, self._placeholder_2)
            self.assertEqual(post_call_kwargs['plugin'].external_link, 'https://www.django-cms.org')
            self.assertEqual(post_call_kwargs['source_language'], 'en')
            self.assertEqual(post_call_kwargs['source_placeholder'], source_placeholder)
            self.assertEqual(post_call_kwargs['source_parent_id'], plugin.parent_id)
            self.assertEqual(post_call_kwargs['target_language'], 'en')
            self.assertEqual(post_call_kwargs['target_placeholder'], self._placeholder_2)
            self.assertEqual(post_call_kwargs['target_parent_id'], None)

    def test_pre_cut_plugin(self):
        user_settings = UserSettings.objects.create(
            language="en",
            user=self._admin_user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        plugin = self._add_plugin()
        endpoint = self.get_move_plugin_uri(plugin)

        data = {
            'plugin_id': plugin.pk,
            'target_language': 'en',
            'placeholder_id': user_settings.clipboard_id,
        }

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            self.assertEqual(call_kwargs['operation'], CUT_PLUGIN)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(call_kwargs['plugin'].placeholder, self._placeholder_1)
            self.assertEqual(call_kwargs['plugin'].external_link, 'https://www.django-cms.org')
            self.assertEqual(call_kwargs['clipboard'], user_settings.clipboard)
            self.assertEqual(call_kwargs['clipboard_language'], 'en')
            self.assertEqual(call_kwargs['source_language'], 'en')
            self.assertEqual(call_kwargs['source_placeholder'], self._placeholder_1)
            self.assertEqual(call_kwargs['source_parent_id'], plugin.parent_id)

    def test_post_cut_plugin(self):
        user_settings = UserSettings.objects.create(
            language="en",
            user=self._admin_user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        plugin = self._add_plugin()
        endpoint = self.get_move_plugin_uri(plugin)

        data = {
            'plugin_id': plugin.pk,
            'target_language': 'en',
            'placeholder_id': user_settings.clipboard_id,
        }

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], CUT_PLUGIN)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(post_call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(post_call_kwargs['plugin'].placeholder, user_settings.clipboard)
            self.assertEqual(post_call_kwargs['plugin'].external_link, 'https://www.django-cms.org')
            self.assertEqual(post_call_kwargs['clipboard'], user_settings.clipboard)
            self.assertEqual(post_call_kwargs['clipboard_language'], 'en')
            self.assertEqual(post_call_kwargs['source_language'], 'en')
            self.assertEqual(post_call_kwargs['source_placeholder'], self._placeholder_1)
            self.assertEqual(post_call_kwargs['source_parent_id'], plugin.parent_id)

    def test_pre_paste_plugin(self):
        user_settings = UserSettings.objects.create(
            language="en",
            user=self._admin_user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        plugin = self._add_plugin(placeholder=user_settings.clipboard)
        endpoint = self.get_move_plugin_uri(plugin)

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': self._placeholder_1.pk,
            'move_a_copy': 'true',
            'target_language': 'en',
            'target_position': 1,
        }

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            self.assertEqual(call_kwargs['operation'], PASTE_PLUGIN)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(call_kwargs['plugin'].placeholder, user_settings.clipboard)
            self.assertEqual(call_kwargs['plugin'].external_link, 'https://www.django-cms.org')
            self.assertEqual(call_kwargs['target_language'], 'en')
            self.assertEqual(call_kwargs['target_placeholder'], self._placeholder_1)
            self.assertEqual(call_kwargs['target_parent_id'], None)

    def test_post_paste_plugin(self):
        user_settings = UserSettings.objects.create(
            language="en",
            user=self._admin_user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        plugin = self._add_plugin(placeholder=user_settings.clipboard)
        endpoint = self.get_move_plugin_uri(plugin)

        data = {
            'plugin_id': plugin.pk,
            'placeholder_id': self._placeholder_1.pk,
            'target_language': 'en',
            'move_a_copy': 'true',
            'target_position': 1,
        }

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], PASTE_PLUGIN)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(post_call_kwargs['plugin'].name, 'A Link')
            self.assertEqual(post_call_kwargs['plugin'].placeholder, self._placeholder_1)
            self.assertEqual(post_call_kwargs['plugin'].external_link, 'https://www.django-cms.org')
            self.assertEqual(post_call_kwargs['target_language'], 'en')
            self.assertEqual(post_call_kwargs['target_placeholder'], self._placeholder_1)
            self.assertEqual(post_call_kwargs['target_parent_id'], None)

    def test_pre_paste_placeholder(self):
        user_settings = UserSettings.objects.create(
            language="en",
            user=self._admin_user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        placeholder_plugin = self._add_plugin(
            user_settings.clipboard,
            'PlaceholderPlugin',
        )
        ref_placeholder = placeholder_plugin.placeholder_ref

        self._add_plugin(ref_placeholder)

        endpoint = self.get_move_plugin_uri(placeholder_plugin)

        data = {
            'plugin_id': placeholder_plugin.pk,
            'placeholder_id': self._placeholder_1.pk,
            'move_a_copy': 'true',
            'target_language': 'en',
            'target_position': 1,
        }

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            plugin = call_kwargs['plugins'][0].get_bound_plugin()

            self.assertEqual(call_kwargs['operation'], PASTE_PLACEHOLDER)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(plugin.name, 'A Link')
            self.assertEqual(plugin.placeholder, ref_placeholder)
            self.assertEqual(plugin.external_link, 'https://www.django-cms.org')
            self.assertEqual(call_kwargs['target_language'], 'en')
            self.assertEqual(call_kwargs['target_placeholder'], self._placeholder_1)

    def test_post_paste_placeholder(self):
        user_settings = UserSettings.objects.create(
            language="en",
            user=self._admin_user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        placeholder_plugin = self._add_plugin(
            user_settings.clipboard,
            'PlaceholderPlugin',
        )
        ref_placeholder = placeholder_plugin.placeholder_ref

        self._add_plugin(ref_placeholder)

        endpoint = self.get_move_plugin_uri(placeholder_plugin)

        data = {
            'plugin_id': placeholder_plugin.pk,
            'placeholder_id': self._placeholder_1.pk,
            'target_language': 'en',
            'move_a_copy': 'true',
            'target_position': 1,
        }

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            plugin = post_call_kwargs['plugins'][0].get_bound_plugin()

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], PASTE_PLACEHOLDER)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(plugin.name, 'A Link')
            self.assertEqual(plugin.placeholder, self._placeholder_1)
            self.assertEqual(plugin.external_link, 'https://www.django-cms.org')
            self.assertEqual(post_call_kwargs['target_language'], 'en')
            self.assertEqual(post_call_kwargs['target_placeholder'], self._placeholder_1)

    def test_pre_add_plugins_from_placeholder(self):
        plugin = self._add_plugin()
        endpoint = self.get_copy_plugin_uri(plugin)
        source_placeholder = plugin.placeholder

        data = {
            'source_language': 'en',
            'source_placeholder_id': self._placeholder_1.pk,
            'target_language': 'de',
            'target_placeholder_id': self._placeholder_2.pk,
        }

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            en_plugin = call_kwargs['plugins'][0].get_bound_plugin()

            self.assertEqual(call_kwargs['operation'], ADD_PLUGINS_FROM_PLACEHOLDER)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(plugin, en_plugin)
            self.assertEqual(call_kwargs['source_language'], 'en')
            self.assertEqual(call_kwargs['source_placeholder'], source_placeholder)
            self.assertEqual(call_kwargs['target_language'], 'de')
            self.assertEqual(call_kwargs['target_placeholder'], self._placeholder_2)

    def test_post_add_plugins_from_placeholder(self):
        plugin = self._add_plugin()
        endpoint = self.get_copy_plugin_uri(plugin)
        source_placeholder = plugin.placeholder

        data = {
            'source_language': 'en',
            'source_placeholder_id': self._placeholder_1.pk,
            'target_language': 'de',
            'target_placeholder_id': self._placeholder_2.pk,
        }

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, data)
                self.assertEqual(response.status_code, 200)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            new_plugin = post_call_kwargs['plugins'][0].get_bound_plugin()

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], ADD_PLUGINS_FROM_PLACEHOLDER)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertNotEqual(plugin, new_plugin)
            self.assertEqual(new_plugin.name, 'A Link')
            self.assertEqual(new_plugin.placeholder, self._placeholder_2)
            self.assertEqual(new_plugin.external_link, 'https://www.django-cms.org')
            self.assertEqual(post_call_kwargs['source_language'], 'en')
            self.assertEqual(post_call_kwargs['source_placeholder'], source_placeholder)
            self.assertEqual(post_call_kwargs['target_language'], 'de')
            self.assertEqual(post_call_kwargs['target_placeholder'], self._placeholder_2)

    def test_pre_clear_placeholder(self):
        plugin = self._add_plugin()
        endpoint = self.get_clear_placeholder_url(self._placeholder_1)

        with signal_tester(pre_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, {'test': 0})
                self.assertEqual(response.status_code, 302)

            self.assertEqual(env.call_count, 1)

            call_kwargs = env.calls[0][1]

            del_plugin = call_kwargs['plugins'][0]

            self.assertEqual(call_kwargs['operation'], CLEAR_PLACEHOLDER)
            self.assertEqual(call_kwargs['language'], 'en')
            self.assertTrue('token' in call_kwargs)
            self.assertEqual(call_kwargs['origin'], '/en/')
            self.assertEqual(del_plugin.pk, plugin.pk)
            self.assertEqual(call_kwargs['placeholder'], self._placeholder_1)

    def test_post_clear_placeholder(self):
        plugin = self._add_plugin()
        endpoint = self.get_clear_placeholder_url(self._placeholder_1)

        with signal_tester(pre_placeholder_operation, post_placeholder_operation) as env:
            with self.login_user_context(self._admin_user):
                response = self.client.post(endpoint, {'test': 0})
                self.assertEqual(response.status_code, 302)

            self.assertEqual(env.call_count, 2)

            pre_call_kwargs = env.calls[0][1]
            post_call_kwargs = env.calls[1][1]

            del_plugin = post_call_kwargs['plugins'][0]

            self.assertTrue('token' in post_call_kwargs)

            self.assertEqual(post_call_kwargs['operation'], CLEAR_PLACEHOLDER)
            self.assertEqual(post_call_kwargs['language'], 'en')
            self.assertTrue(pre_call_kwargs['token'] == post_call_kwargs['token'])
            self.assertEqual(post_call_kwargs['origin'], '/en/')
            self.assertEqual(del_plugin.pk, plugin.pk)
            self.assertEqual(post_call_kwargs['placeholder'], self._placeholder_1)


class AppPlaceholderTestCase(PagePlaceholderTestCase):

    def setUp(self):
        self._admin_user = self.get_superuser()
        self._cms_page = self.create_homepage(
            "home",
            "nav_playground.html",
            "en",
            created_by=self._admin_user,
        )
        self._placeholder_1 = self._cms_page.get_placeholders("en").get(slot='body')
        self._placeholder_2 = self._cms_page.get_placeholders("en").get(slot='right-column')
