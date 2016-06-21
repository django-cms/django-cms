# -*- coding: utf-8 -*-
from django.test.utils import override_settings

from cms.models.permissionmodels import PageUserGroup
from cms.test_utils.testcases import CMSTestCase
from cms.utils.urlutils import admin_reverse


@override_settings(CMS_PERMISSION=True)
class PageUserGroupPermissionsOnTest(CMSTestCase):

    def get_group_dummy_data(self, **kwargs):
        data = {
            'name': 'Test group',
            'can_add_page': 'on',
            'can_change_page': 'on',
            'can_delete_page': 'on',
        }
        data.update(**kwargs)
        return data

    def get_group(self):
        data = {
            'name': 'Test group',
            'created_by': self.get_superuser(),
        }
        return PageUserGroup.objects.create(**data)

    def test_group_in_admin_index(self):
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                '<a href="/en/admin/cms/pageusergroup/">User groups (page)</a>',
                html=True,
            )

        endpoint = self.get_admin_url(PageUserGroup, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)

    def test_group_not_in_admin_index(self):
        endpoint = admin_reverse('app_list', args=['cms'])
        staff_user = self.get_staff_user_with_no_permissions()

        self.add_permission(staff_user, 'change_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)

        endpoint = self.get_admin_url(PageUserGroup, 'changelist')

        with self.login_user_context(staff_user):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 403)

    def test_group_can_add(self):
        endpoint = self.get_admin_url(PageUserGroup, 'add')
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_group_dummy_data()

        self.add_permission(staff_user, 'add_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(PageUserGroup.objects.filter(name='Test group').exists())

    def test_group_cant_add(self):
        endpoint = self.get_admin_url(PageUserGroup, 'add')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_group_dummy_data()

        self.add_permission(staff_user, 'add_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(PageUserGroup.objects.filter(name='Test group').exists())

    def test_group_can_change(self):
        group = self.get_group()
        endpoint = self.get_admin_url(PageUserGroup, 'change', group.pk)
        redirect_to = self.get_admin_url(PageUserGroup, 'changelist')
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_group_dummy_data(name='New test group')

        self.add_permission(staff_user, 'change_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertTrue(PageUserGroup.objects.filter(name='New test group').exists())

    def test_group_cant_change(self):
        group = self.get_group()
        endpoint = self.get_admin_url(PageUserGroup, 'change', group.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        data = self.get_group_dummy_data(name='New test group')

        self.add_permission(staff_user, 'change_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(PageUserGroup.objects.filter(name='Test group').exists())

    def test_group_can_delete(self):
        group = self.get_group()
        endpoint = self.get_admin_url(PageUserGroup, 'delete', group.pk)
        redirect_to = admin_reverse('index')
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_group')
        self.add_permission(staff_user, 'delete_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=True)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertRedirects(response, redirect_to)
            self.assertFalse(PageUserGroup.objects.filter(name='Test group').exists())

    def test_group_cant_delete(self):
        group = self.get_group()
        endpoint = self.get_admin_url(PageUserGroup, 'delete', group.pk)
        staff_user = self.get_staff_user_with_no_permissions()
        data = {'post': 'yes'}

        self.add_permission(staff_user, 'delete_group')
        self.add_permission(staff_user, 'delete_pageusergroup')
        self.add_global_permission(staff_user, can_change_permissions=False)

        with self.login_user_context(staff_user):
            response = self.client.post(endpoint, data)
            self.assertEqual(response.status_code, 403)
            self.assertTrue(PageUserGroup.objects.filter(name='Test group').exists())
