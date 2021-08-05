from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.messages.storage.cookie import CookieStorage
from django.forms.models import model_to_dict
from django.test.utils import override_settings

from cms.models.permissionmodels import PageUser
from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse


class PermissionsOnTestCase(CMSTestCase):

    def _user_exists(self, username=None):
        if PageUser.USERNAME_FIELD != "email":
            username = username or "perms-testuser"
        else:
            username = username or "perms-testuser@django-cms.org"
        query = {PageUser.USERNAME_FIELD: username}
        return PageUser.objects.filter(**query).exists()

    def _get_user_data(self, **kwargs):
        data = {
            'password1': 'changeme',
            'password2': 'changeme',
        }

        if PageUser.USERNAME_FIELD != "email":
            data[PageUser.USERNAME_FIELD] = "perms-testuser"
        else:
            data[PageUser.USERNAME_FIELD] = "perms-testuser@django-cms.org"

        data.update(**kwargs)
        return data

    def _get_delete_perm(self):
        return get_permission_codename('delete', get_user_model()._meta)


@override_settings(CMS_PERMISSION=True)
class PermissionsOnGlobalTest(PermissionsOnTestCase):
    """
    Tests all user interactions with the page user admin
    while permissions are set to True and user has
    global permissions.
    """

    def test_user_in_admin_index(self):
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                '<a href="/en/admin/cms/pageuser/">Users (page)</a>',
                html=True,
            )

        endpoint = self.get_admin_url(PageUser, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

    def test_user_not_in_admin_index(self):
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = admin_reverse('app_list', args=['cms'])

        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)

        endpoint = self.get_admin_url(PageUser, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_add_user(self):
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self._get_user_data()
        data['_addanother'] = '1'

        self.add_permission(staff_user, 'add_pageuser')
        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._user_exists())

    def test_user_cant_add_user(self):
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self._get_user_data()

        self.add_permission(staff_user, 'add_pageuser')
        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._user_exists())

    def test_user_can_change_user(self):
        user = self.get_staff_page_user()
        endpoint = self.get_admin_url(PageUser, 'change', user.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = model_to_dict(user, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        if user.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[user.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._user_exists(username))

    def test_user_cant_change_user(self):
        user = self.get_staff_page_user()
        endpoint = self.get_admin_url(PageUser, 'change', user.pk)
        staff_user = self.get_staff_user_with_no_permissions()

        data = model_to_dict(user, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=False)

        if user.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[user.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._user_exists(username))

    def test_user_can_delete_user(self):
        user = self.get_staff_page_user()
        endpoint = self.get_admin_url(PageUser, 'delete', user.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, self._get_delete_perm())
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._user_exists())

    def test_user_cant_delete_user(self):
        user = self.get_staff_page_user()
        endpoint = self.get_admin_url(PageUser, 'delete', user.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, self._get_delete_perm())
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._user_exists())


@override_settings(CMS_PERMISSION=True)
class PermissionsOnPageTest(PermissionsOnTestCase):
    """
    Tests all user interactions with the page user admin
    while permissions are set to True and user has
    page permissions.
    """

    def setUp(self):
        self._permissions_page = self.get_permissions_test_page()

    def test_user_in_admin_index(self):
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                '<a href="/en/admin/cms/pageuser/">Users (page)</a>',
                html=True,
            )

        endpoint = self.get_admin_url(PageUser, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

    def test_user_not_in_admin_index(self):
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = admin_reverse('app_list', args=['cms'])

        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)

        endpoint = self.get_admin_url(PageUser, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_add_user(self):
        """
        User can add new users if can_change_permissions
        is set to True.
        """
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self._get_user_data()
        data['_addanother'] = '1'

        self.add_permission(staff_user, 'add_pageuser')
        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._user_exists())

    def test_user_cant_add_user(self):
        """
        User can't add new users if can_change_permissions
        is set to False.
        """
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self._get_user_data()

        self.add_permission(staff_user, 'add_pageuser')
        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._user_exists())

    def test_user_can_change_subordinate(self):
        """
        User can change users he created if can_change_permissions
        is set to True.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        subordinate = self.get_staff_page_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'change', subordinate.pk)

        data = model_to_dict(subordinate, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        if subordinate.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[subordinate.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._user_exists(username))

    def test_user_cant_change_subordinate(self):
        """
        User cant change users he created if can_change_permissions
        is set to False.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        subordinate = self.get_staff_page_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'change', subordinate.pk)

        data = model_to_dict(subordinate, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=False,
        )

        if subordinate.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[subordinate.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._user_exists(username))

    def test_user_cant_change_self(self):
        """
        User cant change his own user,
        even with can_change_permissions set to True.
        """
        admin = self.get_superuser()
        staff_user = self.get_staff_page_user(created_by=admin)
        endpoint = self.get_admin_url(PageUser, 'change', staff_user.pk)
        redirect_to = admin_reverse('index')

        data = model_to_dict(staff_user, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        if staff_user.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[staff_user.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            msgs = CookieStorage(response)._decode(response.cookies['messages'].value)
            self.assertTrue(msgs[0], PageUser._meta.verbose_name)
            self.assertTrue(msgs[0], 'ID "%s"' % staff_user.pk)
            self.assertFalse(self._user_exists(username))

    def test_user_cant_change_others(self):
        """
        User cant change a users created by another user,
        even with can_change_permissions set to True.
        """
        admin = self.get_superuser()
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        endpoint = self.get_admin_url(PageUser, 'change', staff_user_2.pk)
        redirect_to = admin_reverse('index')

        data = model_to_dict(staff_user_2, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        if staff_user_2.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[staff_user_2.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            msgs = CookieStorage(response)._decode(response.cookies['messages'].value)
            self.assertTrue(msgs[0], PageUser._meta.verbose_name)
            self.assertTrue(msgs[0], 'ID "%s"' % staff_user_2.pk)
            self.assertFalse(self._user_exists(username))

    def test_user_can_delete_subordinate(self):
        """
        User can delete users he created if can_change_permissions
        is set to True.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        subordinate = self.get_staff_page_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'delete', subordinate.pk)
        redirect_to = admin_reverse('index')
        data = {'post': 'yes'}

        self.add_permission(staff_user, self._get_delete_perm())
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._user_exists())

    def test_user_cant_delete_subordinate(self):
        """
        User cant delete users he created if can_change_permissions
        is set to False.
        """
        staff_user = self.get_staff_user_with_no_permissions()
        subordinate = self.get_staff_page_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'delete', subordinate.pk)
        data = {'post': 'yes'}

        self.add_permission(staff_user, self._get_delete_perm())
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=False,
        )

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._user_exists())

    def test_user_cant_delete_self(self):
        """
        User cant delete his own user,
        even with can_change_permissions set to True.
        """
        admin = self.get_superuser()
        staff_user = self.get_staff_page_user(created_by=admin)
        endpoint = self.get_admin_url(PageUser, 'delete', staff_user.pk)
        redirect_to = admin_reverse('index')
        data = {'post': 'yes'}

        self.add_permission(staff_user, self._get_delete_perm())
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            username = getattr(staff_user, staff_user.USERNAME_FIELD)
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            msgs = CookieStorage(response)._decode(response.cookies['messages'].value)
            self.assertTrue(msgs[0], PageUser._meta.verbose_name)
            self.assertTrue(msgs[0], 'ID "%s"' % staff_user.pk)
            self.assertTrue(self._user_exists(username))

    def test_user_cant_delete_others(self):
        """
        User cant delete a user created by another user,
        even with can_change_permissions set to True.
        """
        admin = self.get_superuser()
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user_2 = self.get_staff_page_user(created_by=admin)
        endpoint = self.get_admin_url(PageUser, 'delete', staff_user_2.pk)
        redirect_to = admin_reverse('index')

        data = {'post': 'yes'}

        self.add_permission(staff_user, self._get_delete_perm())
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            username = getattr(staff_user_2, staff_user_2.USERNAME_FIELD)
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            msgs = CookieStorage(response)._decode(response.cookies['messages'].value)
            self.assertTrue(msgs[0], PageUser._meta.verbose_name)
            self.assertTrue(msgs[0], 'ID "%s"' % staff_user_2.pk)
            self.assertTrue(self._user_exists(username))
