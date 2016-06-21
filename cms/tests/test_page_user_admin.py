# -*- coding: utf-8 -*-
from django.forms.models import model_to_dict
from django.test.utils import override_settings

from cms.api import create_page
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

    def get_staff_page_user(self, created_by):
        user = self._create_user("staff pageuser", is_staff=True, is_superuser=False)
        data = model_to_dict(user, exclude=['groups', 'user_permissions'])
        data['user_ptr'] = user
        data['created_by'] = created_by
        return PageUser.objects.create(**data)

    def get_user_dummy_data(self, **kwargs):
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

    def get_user(self, created_by=None):
        if not created_by:
            created_by = self.get_superuser()

        data = {'created_by': created_by}

        if PageUser.USERNAME_FIELD != "email":
            data[PageUser.USERNAME_FIELD] = "perms-testuser"
        else:
            data[PageUser.USERNAME_FIELD] = "perms-testuser@django-cms.org"

        user = PageUser(**data)
        user.set_password('changeme')
        user.save()
        return user

    def get_page(self):
        admin = self.get_superuser()
        create_page(
            "home",
            "nav_playground.html",
            "en",
            created_by=admin,
            published=True,
        )
        page = create_page(
            "permissions",
            "nav_playground.html",
            "en",
            created_by=admin,
            published=True,
        )
        return page


@override_settings(CMS_PERMISSION=True)
class PermissionsOnGlobalTest(PermissionsOnTestCase):
    """
    Uses GlobalPermission
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

    def test_user_can_add(self):
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_user_dummy_data()
        data['_addanother'] = '1'

        self.add_permission(staff_user, 'add_pageuser')
        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, endpoint)
            self.assertTrue(self._user_exists())

    def test_user_cant_add(self):
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_user_dummy_data()

        self.add_permission(staff_user, 'add_pageuser')
        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(self._user_exists())

    def test_user_can_change(self):
        user = self.get_user()
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

    def test_user_cant_change(self):
        user = self.get_user()
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

    def test_user_can_delete(self):
        user = self.get_user()
        endpoint = self.get_admin_url(PageUser, 'delete', user.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_user')
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertFalse(self._user_exists())

    def test_user_cant_delete(self):
        user = self.get_user()
        endpoint = self.get_admin_url(PageUser, 'delete', user.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_user')
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(self._user_exists())


@override_settings(CMS_PERMISSION=True)
class PermissionsOnPageTest(PermissionsOnTestCase):
    """
    Uses PagePermission
    """

    def setUp(self):
        self._permissions_page = self.get_page()

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
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(
                response,
                '<a href="/en/admin/cms/pageuser/">Users (page)</a>',
                html=True,
            )

        endpoint = self.get_admin_url(PageUser, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_user_can_add(self):
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_user_dummy_data()
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

    def test_user_cant_add(self):
        endpoint = self.get_admin_url(PageUser, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_user_dummy_data()

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
        staff_user = self.get_staff_user_with_no_permissions()
        user = self.get_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'change', user.pk)
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

    def test_user_cant_change_subordinate(self):
        staff_user = self.get_staff_user_with_no_permissions()
        user = self.get_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'change', user.pk)
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

    def test_user_cant_change_self(self):
        staff_user = self.get_staff_user_with_no_permissions()
        endpoint = self.get_admin_url(PageUser, 'change', staff_user.pk)

        data = model_to_dict(staff_user, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        if staff_user.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[staff_user.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 404)
            self.assertFalse(self._user_exists(username))

    def test_user_cant_change_superior(self):
        staff_user = self.get_staff_user_with_no_permissions()
        superior = self.get_superuser()
        endpoint = self.get_admin_url(PageUser, 'change', superior.pk)

        data = model_to_dict(superior, exclude=['date_joined'])
        data['_continue'] = '1'
        data['date_joined_0'] = '2016-06-21'
        data['date_joined_1'] = '15:00:00'

        self.add_permission(staff_user, 'change_pageuser')
        self.add_global_permission(staff_user, can_change_permissions=True)

        if superior.USERNAME_FIELD != "email":
            username = "perms-testuser2"
        else:
            username = "perms-testuser+2@django-cms.org"

        data[superior.USERNAME_FIELD] = username

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 404)
            self.assertFalse(self._user_exists(username))

    def test_user_can_delete_subordinate(self):
        staff_user = self.get_staff_user_with_no_permissions()
        user = self.get_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'delete', user.pk)
        redirect_to = admin_reverse('index')
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_user')
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
        staff_user = self.get_staff_user_with_no_permissions()
        user = self.get_user(created_by=staff_user)
        endpoint = self.get_admin_url(PageUser, 'delete', user.pk)
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_user')
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
        admin = self.get_superuser()
        staff_user = self.get_staff_page_user(created_by=admin)
        endpoint = self.get_admin_url(PageUser, 'delete', staff_user.pk)
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_user')
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            username = getattr(staff_user, staff_user.USERNAME_FIELD)
            response = self.client.post(endpoint, data)
            # The response is a 404 instead of a 403
            # because the queryset is limited to objects
            # that the user has permissions for.
            # This queryset is used to fetch the object
            # from the request, resulting in a 404.
            self.assertEqual(response.status_code, 404)
            self.assertTrue(self._user_exists(username))

    def test_user_cant_delete_superior(self):
        admin = self.get_superuser()
        superior = self.get_staff_page_user(created_by=admin)
        endpoint = self.get_admin_url(PageUser, 'delete', superior.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_user')
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_page_permission(
            staff_user,
            self._permissions_page,
            can_change_permissions=True,
        )

        with self.login_user_context(staff_user):
            username = getattr(superior, superior.USERNAME_FIELD)
            response = self.client.post(endpoint, data)
            # The response is a 404 instead of a 403
            # because the queryset is limited to objects
            # that the user has permissions for.
            # This queryset is used to fetch the object
            # from the request, resulting in a 404.
            self.assertEqual(response.status_code, 404)
            self.assertTrue(self._user_exists(username))
