from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages.storage.cookie import CookieStorage
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.test.utils import override_settings

from cms.api import create_page
from cms.models.permissionmodels import ACCESS_PAGE_AND_DESCENDANTS, GlobalPagePermission, PageUser
from cms.test_utils.testcases import CMSTestCase
from cms.utils.permissions import get_subordinate_groups, get_subordinate_users
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


@override_settings(CMS_PERMISSION=True)
class SuperuserProtectionTest(PermissionsOnTestCase):
    """
    A superuser is nobody's subordinate. A staff user holding the cms user
    permissions plus can_change_permissions must not be able to manage - and
    thereby take over - a superuser account.
    """

    def _get_superuser_page_user(self):
        parent_link_field = list(PageUser._meta.parents.values())[0]
        user = self._create_user('perms-superuser', is_staff=True, is_superuser=True)
        data = model_to_dict(user, exclude=['groups', 'user_permissions'])
        data[parent_link_field.name] = user
        data['created_by'] = user
        page_user = PageUser.objects.create(**data)
        page_user.set_password('original-password')
        page_user.save()
        return page_user

    def _get_delegated_admin(self):
        staff_user = self.get_staff_user_with_no_permissions()
        self.add_permission(staff_user, 'change_pageuser')
        self.add_permission(staff_user, 'delete_pageuser')
        self.add_permission(staff_user, self._get_delete_perm())
        self.add_global_permission(staff_user, can_change_permissions=True)
        return staff_user

    def test_superuser_not_subordinate_to_delegated_admin(self):
        site = Site.objects.get_current()
        superuser = self._get_superuser_page_user()
        staff_user = self._get_delegated_admin()

        subordinates = get_subordinate_users(staff_user, site)
        self.assertNotIn(superuser.pk, subordinates.values_list('pk', flat=True))

    def test_superuser_sees_superuser_as_subordinate(self):
        site = Site.objects.get_current()
        superuser = self._get_superuser_page_user()

        subordinates = get_subordinate_users(self.get_superuser(), site)
        self.assertIn(superuser.pk, subordinates.values_list('pk', flat=True))

    def test_superuser_hidden_from_changelist(self):
        superuser = self._get_superuser_page_user()
        staff_user = self._get_delegated_admin()
        endpoint = self.get_admin_url(PageUser, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(
                response,
                getattr(superuser, superuser.USERNAME_FIELD),
            )

    def test_delegated_admin_cant_open_superuser_change_view(self):
        superuser = self._get_superuser_page_user()
        staff_user = self._get_delegated_admin()
        endpoint = self.get_admin_url(PageUser, 'change', superuser.pk)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 302)

    def test_delegated_admin_cant_change_superuser_password(self):
        superuser = self._get_superuser_page_user()
        staff_user = self._get_delegated_admin()
        endpoint = self.get_admin_url(PageUser, 'change', superuser.pk)
        endpoint = endpoint.replace('/change/', '/password/')

        data = {
            'password1': 'hijacked-password',
            'password2': 'hijacked-password',
            'usable_password': 'true',
        }

        with self.login_user_context(staff_user):
            # 404 rather than 403: the superuser is not in the admin's
            # queryset at all, so it does not even leak its existence.
            self.assertEqual(self.client.get(endpoint).status_code, 404)
            self.assertEqual(self.client.post(endpoint, data).status_code, 404)

        superuser.refresh_from_db()
        self.assertFalse(superuser.check_password('hijacked-password'))
        self.assertTrue(superuser.check_password('original-password'))

    def test_admin_denies_change_permission_on_superuser(self):
        """
        Second line of defence, for the case where the admin's queryset is
        widened again: the object level checks refuse a superuser outright.
        """
        superuser = self._get_superuser_page_user()
        staff_user = self._get_delegated_admin()
        model_admin = admin.site._registry[PageUser]
        request = self.get_request()
        request.user = staff_user

        self.assertFalse(model_admin.has_change_permission(request, superuser))
        self.assertFalse(model_admin.has_view_permission(request, superuser))
        self.assertFalse(model_admin.has_delete_permission(request, superuser))

        with self.assertRaises(PermissionDenied):
            with patch.object(model_admin, 'get_object', return_value=superuser):
                model_admin.user_change_password(request, str(superuser.pk))

    def test_superuser_can_change_superuser_password(self):
        superuser = self._get_superuser_page_user()
        endpoint = self.get_admin_url(PageUser, 'change', superuser.pk)
        endpoint = endpoint.replace('/change/', '/password/')

        data = {
            'password1': 'a-new-password',
            'password2': 'a-new-password',
            'usable_password': 'true',
        }

        with self.login_user_context(self.get_superuser()):
            self.assertEqual(self.client.get(endpoint).status_code, 200)
            self.assertEqual(self.client.post(endpoint, data).status_code, 302)

        superuser.refresh_from_db()
        self.assertTrue(superuser.check_password('a-new-password'))

    def test_delegated_admin_cant_delete_superuser(self):
        superuser = self._get_superuser_page_user()
        staff_user = self._get_delegated_admin()
        endpoint = self.get_admin_url(PageUser, 'delete', superuser.pk)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, {'post': 'yes'})
            self.assertEqual(response.status_code, 302)

        self.assertTrue(PageUser.objects.filter(pk=superuser.pk).exists())


class SubordinatesTestMixin:

    def _get_page_user(self, username, created_by=None):
        parent_link_field = list(PageUser._meta.parents.values())[0]
        user = self._create_user(username, is_staff=True)
        data = model_to_dict(user, exclude=['groups', 'user_permissions'])
        data[parent_link_field.name] = user
        data['created_by'] = created_by or self.get_superuser()
        page_user = PageUser.objects.create(**data)
        page_user.set_password('original-password')
        page_user.save()
        return page_user

    def _get_password_url(self, user):
        change_url = self.get_admin_url(PageUser, 'change', user.pk)
        self.assertTrue(change_url.endswith('/change/'))
        return change_url[:-len('change/')] + 'password/'

    def _global_grant(self, sites, **kwargs):
        grant = GlobalPagePermission.objects.create(can_change=True, **kwargs)
        grant.sites.set(sites)
        return grant

    def _subordinate_user_ids(self, site=None):
        return set(get_subordinate_users(self.manager, site or self.site1).values_list('pk', flat=True))

    def _subordinate_group_ids(self):
        return set(get_subordinate_groups(self.manager, self.site1).values_list('pk', flat=True))


@override_settings(CMS_PERMISSION=True)
class SiteScopedSubordinatesTest(SubordinatesTestMixin, PermissionsOnTestCase):
    """
    Global permissions on one site put a user at the top of the hierarchy of
    that site only. Accounts and groups holding permissions on another site -
    or on all sites - are not subordinate: being able to manage such an account
    (set its password, for one) means taking over its rights on a site the
    manager has no authority on.
    """

    def setUp(self):
        self.site1 = Site.objects.get_current()
        self.site2 = Site.objects.create(domain='site2.example.com', name='site2')
        self.manager = self._create_user('site1-manager', is_staff=True)
        self.add_permission(self.manager, 'change_pageuser')
        self.add_permission(self.manager, 'delete_pageuser')
        self.add_permission(self.manager, self._get_delete_perm())
        self.manager_grant = GlobalPagePermission.objects.create(
            user=self.manager, can_change=True, can_change_permissions=True,
        )
        self.manager_grant.sites.set([self.site1])

    def test_user_with_global_permission_on_other_site_not_subordinate(self):
        target = self._get_page_user('site2-user')
        self._global_grant([self.site2], user=target)
        self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_user_with_global_permission_on_all_sites_not_subordinate(self):
        target = self._get_page_user('all-sites-user')
        self._global_grant([], user=target)
        self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_user_with_global_permission_on_both_sites_not_subordinate(self):
        target = self._get_page_user('both-sites-user')
        self._global_grant([self.site1, self.site2], user=target)
        self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_user_with_page_permission_on_other_site_not_subordinate(self):
        target = self._get_page_user('site2-page-user')
        page = create_page('site2 page', 'nav_playground.html', 'de', site=self.site2)
        self.add_page_permission(target, page, can_change=True)
        self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_user_with_group_permission_on_other_site_not_subordinate(self):
        target = self._get_page_user('site2-group-user')
        global_group = Group.objects.create(name='site2 global')
        self._global_grant([self.site2], group=global_group)
        page_group = Group.objects.create(name='site2 page')
        page = create_page('site2 page', 'nav_playground.html', 'de', site=self.site2)
        self.add_page_permission(None, page, group=page_group, can_change=True)
        bystander = self._get_page_user('site2-page-group-user')
        target.groups.add(global_group)
        bystander.groups.add(page_group)

        subordinates = self._subordinate_user_ids()
        self.assertNotIn(target.pk, subordinates)
        self.assertNotIn(bystander.pk, subordinates)
        groups = self._subordinate_group_ids()
        self.assertNotIn(global_group.pk, groups)
        self.assertNotIn(page_group.pk, groups)

    def test_users_within_managed_site_stay_subordinate(self):
        global_user = self._get_page_user('site1-global-user')
        self._global_grant([self.site1], user=global_user)
        page_user = self._get_page_user('site1-page-user')
        page = create_page('site1 page', 'nav_playground.html', 'en', site=self.site1)
        self.add_page_permission(page_user, page, can_change=True)
        unassigned = self._get_page_user('unassigned-user')
        group = Group.objects.create(name='site1 group')
        self._global_grant([self.site1], group=group)

        subordinates = self._subordinate_user_ids()
        self.assertIn(global_user.pk, subordinates)
        self.assertIn(page_user.pk, subordinates)
        self.assertIn(unassigned.pk, subordinates)
        self.assertIn(group.pk, self._subordinate_group_ids())

    def test_manager_of_all_sites_sees_users_of_every_site(self):
        target = self._get_page_user('site2-user')
        self._global_grant([self.site2], user=target)
        everywhere = self._get_page_user('all-sites-user')
        self._global_grant([], user=everywhere)
        group = Group.objects.create(name='site2 group')
        self._global_grant([self.site2], group=group)

        self.manager_grant.sites.clear()

        for site in (self.site1, self.site2):
            subordinates = self._subordinate_user_ids(site)
            self.assertIn(target.pk, subordinates)
            self.assertIn(everywhere.pk, subordinates)
        self.assertIn(group.pk, self._subordinate_group_ids())

    def test_manager_of_both_sites_sees_users_of_both(self):
        target = self._get_page_user('site2-user')
        self._global_grant([self.site2], user=target)
        self._global_grant([self.site2], user=self.manager, can_change_permissions=True)
        self.assertIn(target.pk, self._subordinate_user_ids())

    def test_cannot_take_over_account_of_other_site(self):
        target = self._get_page_user('site2-user')
        self._global_grant([self.site2], user=target, can_change_permissions=True)
        change_url = self.get_admin_url(PageUser, 'change', target.pk)
        password_url = self._get_password_url(target)
        delete_url = self.get_admin_url(PageUser, 'delete', target.pk)
        data = {'password1': 'taken-over-123', 'password2': 'taken-over-123'}

        with self.login_user_context(self.manager):
            response = self.client.get(self.get_admin_url(PageUser, 'changelist'))
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(target.pk, [obj.pk for obj in response.context['cl'].result_list])
            self.assertNotEqual(self.client.get(change_url).status_code, 200)
            self.assertNotEqual(self.client.post(password_url, data).status_code, 200)
            self.client.post(delete_url, {'post': 'yes'})

        target = PageUser.objects.get(pk=target.pk)
        self.assertTrue(target.check_password('original-password'))

    def test_can_still_manage_account_of_own_site(self):
        target = self._get_page_user('site1-user')
        self._global_grant([self.site1], user=target)
        password_url = self._get_password_url(target)
        data = {'password1': 'changed-by-manager-123', 'password2': 'changed-by-manager-123'}

        with self.login_user_context(self.manager):
            self.assertEqual(self.client.post(password_url, data).status_code, 302)

        target = PageUser.objects.get(pk=target.pk)
        self.assertTrue(target.check_password('changed-by-manager-123'))


@override_settings(CMS_PERMISSION=True)
class PageScopedSubordinatesTest(SubordinatesTestMixin, PermissionsOnTestCase):
    """
    A manager whose authority comes from a page permission manages the users
    and groups of that part of the page tree. Accounts and groups also holding
    permissions beyond it - a global permission, or a page permission higher
    up, in another branch or on another site - are not subordinate.
    """

    def setUp(self):
        self.site1 = Site.objects.get_current()
        self.site2 = Site.objects.create(domain='site2.example.com', name='site2')
        self.root = create_page('root', 'nav_playground.html', 'en', site=self.site1)
        self.branch = create_page('branch', 'nav_playground.html', 'en', parent=self.root)
        self.leaf = create_page('leaf', 'nav_playground.html', 'en', parent=self.branch)
        self.other_branch = create_page('other branch', 'nav_playground.html', 'en', parent=self.root)
        self.site2_page = create_page('site2 page', 'nav_playground.html', 'de', site=self.site2)

        self.manager = self._create_user('branch-manager', is_staff=True)
        self.add_permission(self.manager, 'change_pageuser')
        self.add_permission(self.manager, 'delete_pageuser')
        self.add_permission(self.manager, self._get_delete_perm())
        self.add_page_permission(
            self.manager, self.branch, can_change=True, can_change_permissions=True,
            grant_on=ACCESS_PAGE_AND_DESCENDANTS,
        )

    def _get_leaf_user(self, username):
        user = self._get_page_user(username)
        self.add_page_permission(user, self.leaf, can_change=True)
        return user

    def test_user_within_managed_pages_is_subordinate(self):
        target = self._get_leaf_user('leaf-user')
        unassigned = self._get_page_user('unassigned-user', created_by=self.manager)
        group = Group.objects.create(name='leaf group')
        self.add_page_permission(None, self.leaf, group=group, can_change=True)

        subordinates = self._subordinate_user_ids()
        self.assertIn(target.pk, subordinates)
        self.assertIn(unassigned.pk, subordinates)
        self.assertIn(group.pk, self._subordinate_group_ids())

    def test_user_with_global_permission_not_subordinate(self):
        for sites in ([], [self.site1], [self.site2]):
            with self.subTest(sites=sites):
                target = self._get_leaf_user(f'leaf-user-{len(sites)}-{sites[0].pk if sites else 0}')
                self._global_grant(sites, user=target)
                self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_unassigned_user_with_global_permission_not_subordinate(self):
        target = self._get_page_user('unassigned-user', created_by=self.manager)
        self._global_grant([self.site1], user=target)
        self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_user_with_page_permission_beyond_managed_pages_not_subordinate(self):
        for page in (self.root, self.other_branch, self.site2_page):
            with self.subTest(page=page.pk):
                target = self._get_leaf_user(f'leaf-user-{page.pk}')
                self.add_page_permission(target, page, can_change=True)
                self.assertNotIn(target.pk, self._subordinate_user_ids())

    def test_user_with_group_permission_beyond_managed_pages_not_subordinate(self):
        global_group = Group.objects.create(name='global group')
        self._global_grant([self.site1], group=global_group)
        page_group = Group.objects.create(name='other branch group')
        self.add_page_permission(None, self.other_branch, group=page_group, can_change=True)
        self.add_page_permission(None, self.leaf, group=page_group, can_change=True)

        for group in (global_group, page_group):
            with self.subTest(group=group.name):
                target = self._get_leaf_user(f'leaf-user-{group.pk}')
                target.groups.add(group)
                self.assertNotIn(target.pk, self._subordinate_user_ids())
                self.assertNotIn(group.pk, self._subordinate_group_ids())

    def test_cannot_take_over_account_beyond_managed_pages(self):
        target = self._get_leaf_user('leaf-user')
        self._global_grant([self.site1], user=target, can_change_permissions=True)
        data = {'password1': 'taken-over-123', 'password2': 'taken-over-123'}

        with self.login_user_context(self.manager):
            self.assertNotEqual(self.client.get(self.get_admin_url(PageUser, 'change', target.pk)).status_code, 200)
            self.assertNotEqual(self.client.post(self._get_password_url(target), data).status_code, 200)
            self.client.post(self.get_admin_url(PageUser, 'delete', target.pk), {'post': 'yes'})

        target = PageUser.objects.get(pk=target.pk)
        self.assertTrue(target.check_password('original-password'))

    def test_can_still_manage_account_within_managed_pages(self):
        target = self._get_leaf_user('leaf-user')
        data = {'password1': 'changed-by-manager-123', 'password2': 'changed-by-manager-123'}

        with self.login_user_context(self.manager):
            self.assertEqual(self.client.post(self._get_password_url(target), data).status_code, 302)

        target = PageUser.objects.get(pk=target.pk)
        self.assertTrue(target.check_password('changed-by-manager-123'))
