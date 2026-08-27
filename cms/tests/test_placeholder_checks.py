from unittest.mock import Mock, call, patch

from django.forms.models import model_to_dict

from cms.api import create_page
from cms.models import Placeholder, UserSettings, fields
from cms.models.fields import PlaceholderRelationField
from cms.test_utils.testcases import CMSTestCase


class ChecksTestCase(CMSTestCase):

    def test_no_check_means_passed(self):
        superuser = self.get_superuser()
        field = PlaceholderRelationField()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')
        mock = Mock(return_value=[])
        with patch.object(PlaceholderRelationField, 'checks', property(mock)):
            self.assertTrue(field.run_checks(placeholder, superuser))

    def test_checks(self):
        """Test that PlaceholderRelationField.checks combines
        default_checks with field-level checks.
        """
        check1 = Mock(return_value=True)
        check2 = Mock(return_value=True)
        check3 = Mock(return_value=True)
        field = PlaceholderRelationField(checks=[check2, check3])
        with patch.object(field, 'default_checks', [check1]):
            self.assertEqual(
                list(field.checks),
                [check1, check2, check3],
            )

    def test_checks_one_false(self):
        """Test that one False value short-circuits.
        """

        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')

        check1 = Mock(return_value=False)
        check2 = Mock(return_value=True)
        field = PlaceholderRelationField(checks=[check1, check2])
        self.assertFalse(field.run_checks(placeholder, superuser))
        check1.assert_called_once_with(placeholder, superuser)
        check2.assert_not_called()


class ChecksPlaceholderInterfaceTestCase(CMSTestCase):

    def test_check_source(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')
        check = Mock(return_value=True)
        mock = Mock(return_value=[check])
        with patch.object(PlaceholderRelationField, 'checks', property(mock)):
            self.assertTrue(placeholder.check_source(superuser))
        check.assert_called_once_with(placeholder, superuser)

    def test_check_source_when_source_is_empty(self):
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot='test')
        check = Mock(return_value=True)
        mock = Mock(return_value=[check])
        with patch.object(PlaceholderRelationField, 'checks', property(mock)):
            self.assertTrue(placeholder.check_source(superuser))
        check.assert_not_called()


class ClipboardPermissionTestCase(CMSTestCase):
    """A clipboard is private: only its owner may work with it."""

    def _get_clipboard(self, user):
        user_settings = UserSettings.objects.create(
            language='en',
            user=user,
            clipboard=Placeholder.objects.create(slot='clipboard'),
        )
        user_settings.clipboard.source = user_settings
        user_settings.clipboard.save()
        return user_settings.clipboard

    def test_owner_has_permission(self):
        user = self.get_staff_user_with_no_permissions()
        clipboard = self._get_clipboard(user)

        self.assertTrue(clipboard.has_change_permission(user))
        self.assertTrue(clipboard.check_source(user))

    def test_other_user_has_no_permission(self):
        owner = self.get_staff_user_with_no_permissions()
        other = self._create_user('other', is_staff=True, is_superuser=False)
        clipboard = self._get_clipboard(owner)

        self.assertFalse(clipboard.has_change_permission(other))
        self.assertFalse(clipboard.check_source(other))

    def test_superuser_has_permission(self):
        owner = self.get_staff_user_with_no_permissions()
        superuser = self.get_superuser()
        clipboard = self._get_clipboard(owner)

        self.assertTrue(clipboard.has_change_permission(superuser))
        self.assertTrue(clipboard.check_source(superuser))


class ChecksUsedInAdminEndpointsTestCase(CMSTestCase):

    def setUp(self):
        self.check = Mock(return_value=True)
        self.original_checks = fields.PlaceholderRelationField.default_checks
        fields.PlaceholderRelationField.default_checks = self.original_checks + [self.check]

    def tearDown(self):
        fields.PlaceholderRelationField.default_checks = self.original_checks

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

    def test_add_plugin_to_placeholder_without_source(self):
        superuser = self.get_superuser()
        placeholder = Placeholder.objects.create(slot='test')
        uri = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='LinkPlugin',
            language='en',
        )

        with self.login_user_context(superuser):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
            self.client.post(uri, data)
        self.check.assert_not_called()

    def test_add_plugin(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')
        uri = self.get_add_plugin_uri(
            placeholder=placeholder,
            plugin_type='LinkPlugin',
            language='en',
        )

        with self.login_user_context(superuser):
            data = {'name': 'A Link', 'external_link': 'https://www.django-cms.org'}
            self.client.post(uri, data)
        self.check.assert_called_once_with(placeholder, superuser)

    def test_copy_plugins_to_clipboard(self):
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot='test')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        uri = self.get_copy_plugin_uri(source_plugin)
        user_settings = UserSettings.objects.create(
            language='en',
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )

        with self.login_user_context(superuser):
            data = {
                'source_language': 'en',
                'source_placeholder_id': source_placeholder.pk,
                'source_plugin_id': source_plugin.pk,
                'target_language': 'en',
                'target_placeholder_id': user_settings.clipboard.pk,
            }
            self.client.post(uri, data)

        self.check.assert_not_called()

    def test_copy_placeholder_to_clipboard(self):
        superuser = self.get_superuser()
        source_placeholder = Placeholder.objects.create(slot='test')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        uri = self.get_copy_plugin_uri(source_plugin)
        user_settings = UserSettings.objects.create(
            language='en',
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )

        with self.login_user_context(superuser):
            data = {
                'source_language': "en",
                'source_placeholder_id': source_placeholder.pk,
                'target_language': "en",
                'target_placeholder_id': user_settings.clipboard.pk,
            }
            self.client.post(uri, data)

        self.check.assert_not_called()

    def test_copy_plugin_to_clipboard_from_immutable_source(self):
        """Copying only reads the source, so a non-editable source is allowed."""
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        source_placeholder = page.get_placeholders('en').get(slot='body')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        uri = self.get_copy_plugin_uri(source_plugin)
        user_settings = UserSettings.objects.create(
            language='en',
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        self.check.return_value = False

        with self.login_user_context(superuser):
            data = {
                'source_language': 'en',
                'source_placeholder_id': source_placeholder.pk,
                'source_plugin_id': source_plugin.pk,
                'target_language': 'en',
                'target_placeholder_id': user_settings.clipboard.pk,
            }
            response = self.client.post(uri, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user_settings.clipboard.get_plugins('en').count(), 1)

    def test_copy_placeholder_to_clipboard_from_immutable_source(self):
        """Copying only reads the source, so a non-editable source is allowed."""
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        source_placeholder = page.get_placeholders('en').get(slot='body')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        uri = self.get_copy_plugin_uri(source_plugin)
        user_settings = UserSettings.objects.create(
            language='en',
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )
        self.check.return_value = False

        with self.login_user_context(superuser):
            data = {
                'source_language': "en",
                'source_placeholder_id': source_placeholder.pk,
                'target_language': "en",
                'target_placeholder_id': user_settings.clipboard.pk,
            }
            response = self.client.post(uri, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user_settings.clipboard.get_plugins('en').count(), 1)

    def test_paste_plugin_from_immutable_source(self):
        """Pasting only reads the source, so a non-editable source is allowed."""
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        source_placeholder = page.get_placeholders('en').get(slot='body')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        target_placeholder = Placeholder.objects.create(slot='target')
        uri = self.get_move_plugin_uri(source_plugin)
        self.check.return_value = False

        with self.login_user_context(superuser):
            data = {
                'plugin_id': source_plugin.pk,
                'placeholder_id': target_placeholder.pk,
                'move_a_copy': 'true',
                'target_language': 'en',
                'target_position': 1,
            }
            response = self.client.post(uri, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(target_placeholder.get_plugins('en').count(), 1)
        # The source is untouched: pasting copies, it does not move.
        self.assertEqual(source_placeholder.get_plugins('en').count(), 1)

    def test_copy_plugins_to_placeholder_without_source(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        source_placeholder = page.get_placeholders('en').get(slot='body')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        target_placeholder = Placeholder.objects.create(slot='test')
        uri = self.get_copy_plugin_uri(source_plugin)

        with self.login_user_context(superuser):
            data = {
                'source_language': "en",
                'source_placeholder_id': source_placeholder.pk,
                'source_plugin_id': source_plugin.pk,
                'target_language': "en",
                'target_placeholder_id': target_placeholder.pk,
            }
            self.client.post(uri, data)
        self.check.assert_not_called()

    def test_edit_plugin(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')
        plugin = self._add_plugin_to_placeholder(placeholder)
        uri = self.get_change_plugin_uri(plugin)

        with self.login_user_context(superuser):
            data = model_to_dict(plugin, fields=['name', 'external_link'])
            data['name'] = 'Contents modified'
            self.client.post(uri, data)

        self.check.assert_called_once_with(placeholder, superuser)

    def test_move_plugin(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        page2 = create_page('test', 'nav_playground.html', 'en')
        source_placeholder = page.get_placeholders('en').get(slot='body')
        target_placeholder = page2.get_placeholders('en').get(slot='body')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        uri = self.get_move_plugin_uri(source_plugin)

        with self.login_user_context(superuser):
            data = self._get_move_data(
                source_plugin,
                position=1,
                placeholder=target_placeholder,
            )
            self.client.post(uri, data)

        self.assertEqual(self.check.call_count, 2)
        self.check.assert_has_calls([
            call(source_placeholder, superuser),
            call(target_placeholder, superuser),
        ])

    def test_cut_plugin(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        source_placeholder = page.get_placeholders('en').get(slot='body')
        source_plugin = self._add_plugin_to_placeholder(source_placeholder)
        uri = self.get_move_plugin_uri(source_plugin)
        user_settings = UserSettings.objects.create(
            language='en',
            user=superuser,
            clipboard=Placeholder.objects.create(),
        )

        with self.login_user_context(superuser):
            data = self._get_move_data(
                source_plugin,
                position=1,
                placeholder=user_settings.clipboard,
            )
            self.client.post(uri, data)

        self.check.assert_called_once_with(source_placeholder, superuser)

    def test_delete_plugin(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')
        plugin = self._add_plugin_to_placeholder(placeholder)
        uri = self.get_delete_plugin_uri(plugin)

        with self.login_user_context(superuser):
            data = {'post': True}
            self.client.post(uri, data)

        self.check.assert_called_once_with(placeholder, superuser)

    def test_clear_placeholder(self):
        superuser = self.get_superuser()
        page = create_page('test', 'nav_playground.html', 'en')
        placeholder = page.get_placeholders('en').get(slot='body')
        uri = self.get_clear_placeholder_url(placeholder)

        with self.login_user_context(superuser):
            data = {'test': 0}
            self.client.post(uri, data)

        self.check.assert_called_once_with(placeholder, superuser)
