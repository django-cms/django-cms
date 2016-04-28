# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache

from cms.admin import forms
from cms.admin.forms import (PageUserForm, PagePermissionInlineAdminForm,
                             ViewRestrictionInlineAdminForm, GlobalPagePermissionAdminForm,
                             PageUserGroupForm)
from cms.api import create_page, create_page_user, assign_user_to_page
from cms.forms.fields import PageSelectFormField, SuperLazyIterator

from cms.models import ACCESS_PAGE, ACCESS_PAGE_AND_CHILDREN

from cms.forms.utils import update_site_and_page_choices, get_site_choices, get_page_choices
from cms.forms.widgets import ApplicationConfigSelect
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE_PERMISSION_CHANGE, URL_CMS_PAGE_PERMISSIONS
)
from cms.utils.permissions import set_current_user


class Mock_PageSelectFormField(PageSelectFormField):
    def __init__(self, required=False):
        # That's to have a proper mock object, without having to resort
        # to dirtier tricks. We want to test *just* compress here.
        self.required = required
        self.error_messages = {}
        self.error_messages['invalid_page'] = 'Invalid_page'


class FormsTestCase(CMSTestCase):
    def setUp(self):
        cache.clear()

    def test_get_site_choices(self):
        result = get_site_choices()
        self.assertEqual(result, [])

    def test_get_page_choices(self):
        result = get_page_choices()
        self.assertEqual(result, [('', '----')])

    def test_get_site_choices_without_moderator(self):
        result = get_site_choices()
        self.assertEqual(result, [])

    def test_get_site_choices_without_moderator_with_superuser(self):
        # boilerplate (creating a page)
        User = get_user_model()

        fields = dict(is_staff=True, is_active=True, is_superuser=True, email="super@super.com")

        if User.USERNAME_FIELD != 'email':
            fields[User.USERNAME_FIELD] = "super"

        user_super = User(**fields)
        user_super.set_password(getattr(user_super, User.USERNAME_FIELD))
        user_super.save()
        with self.login_user_context(user_super):
            create_page("home", "nav_playground.html", "en", created_by=user_super)
            # The proper test
            result = get_site_choices()
            self.assertEqual(result, [(1, 'example.com')])

    def test_compress_function_raises_when_page_is_none(self):
        raised = False
        try:
            fake_field = Mock_PageSelectFormField(required=True)
            data_list = (0, None)  #(site_id, page_id) dsite-id is not used
            fake_field.compress(data_list)
            self.fail('compress function didn\'t raise!')
        except forms.ValidationError:
            raised = True
        self.assertTrue(raised)

    def test_compress_function_returns_none_when_not_required(self):
        fake_field = Mock_PageSelectFormField(required=False)
        data_list = (0, None)  #(site_id, page_id) dsite-id is not used
        result = fake_field.compress(data_list)
        self.assertEqual(result, None)

    def test_compress_function_returns_none_when_no_data_list(self):
        fake_field = Mock_PageSelectFormField(required=False)
        data_list = None
        result = fake_field.compress(data_list)
        self.assertEqual(result, None)

    def test_compress_function_gets_a_page_when_one_exists(self):
        # boilerplate (creating a page)
        User = get_user_model()

        fields = dict(is_staff=True, is_active=True, is_superuser=True, email="super@super.com")

        if User.USERNAME_FIELD != 'email':
            fields[User.USERNAME_FIELD] = "super"

        user_super = User(**fields)
        user_super.set_password(getattr(user_super, User.USERNAME_FIELD))
        user_super.save()

        with self.login_user_context(user_super):
            home_page = create_page("home", "nav_playground.html", "en", created_by=user_super)
            # The actual test
            fake_field = Mock_PageSelectFormField()
            data_list = (0, home_page.pk)  #(site_id, page_id) dsite-id is not used
            result = fake_field.compress(data_list)
            self.assertEqual(home_page, result)

    def test_update_site_and_page_choices(self):
        Site.objects.all().delete()
        site = Site.objects.create(domain='http://www.django-cms.org', name='Django CMS', pk=1)
        page1 = create_page('Page 1', 'nav_playground.html', 'en', site=site)
        page2 = create_page('Page 2', 'nav_playground.html', 'de', site=site)
        page3 = create_page('Page 3', 'nav_playground.html', 'en',
                            site=site, parent=page1)
        # Check for injection attacks
        page4 = create_page('Page 4<script>alert("bad-things");</script>',
                            'nav_playground.html', 'en',
                            site=site, parent=page1)
        # enforce the choices to be casted to a list
        site_choices, page_choices = [list(bit) for bit in update_site_and_page_choices('en')]
        self.assertEqual(page_choices, [
            ('', '----'),
            (site.name, [
                (page1.pk, 'Page 1'),
                (page3.pk, '&nbsp;&nbsp;Page 3'),
                (page4.pk, '&nbsp;&nbsp;Page 4&lt;script&gt;alert(&quot;bad-things&quot;);&lt;/script&gt;'),
                (page2.pk, 'Page 2'),
            ])
        ])
        self.assertEqual(site_choices, [(site.pk, site.name)])

    def test_app_config_select_escaping(self):
        class FakeAppConfig(object):
            def __init__(self, pk, config):
                self.pk = pk
                self.config = config

            def __str__(self):
                return self.config

        class FakeApp(object):
            def __init__(self, name, configs=()):
                self.name = name
                self.configs = configs

            def __str__(self):
                return self.name

            def get_configs(self):
                return self.configs

            def get_config_add_url(self):
                return "/fake/url/"

        GoodApp = FakeApp('GoodApp', [
            FakeAppConfig(1, 'good-app-one-config'),
            FakeAppConfig(2, 'good-app-two-config'),
        ])

        BadApp = FakeApp('BadApp', [
            FakeAppConfig(1, 'bad-app-one-config'),
            FakeAppConfig(2, 'bad-app-two-config<script>alert("bad-stuff");</script>'),
        ])

        app_configs = {
            GoodApp: GoodApp,
            BadApp: BadApp,
        }

        app_config_select = ApplicationConfigSelect(app_configs=app_configs)
        output = app_config_select.render('application_configurations', 1)
        self.assertFalse('<script>alert("bad-stuff");</script>' in output)
        self.assertTrue('\\u0026lt\\u003Bscript\\u0026gt\\u003Balert('
                        '\\u0026quot\\u003Bbad\\u002Dstuff\\u0026quot'
                        '\\u003B)\\u003B\\u0026lt\\u003B/script\\u0026gt'
                        '\\u003B' in output)

    def test_superlazy_iterator_behaves_properly_for_sites(self):
        normal_result = get_site_choices()
        lazy_result = SuperLazyIterator(get_site_choices)

        self.assertEqual(normal_result, list(lazy_result))

    def test_superlazy_iterator_behaves_properly_for_pages(self):
        normal_result = get_page_choices()
        lazy_result = SuperLazyIterator(get_page_choices)

        self.assertEqual(normal_result, list(lazy_result))

    def test_page_user_form_initial(self):
        if get_user_model().USERNAME_FIELD == 'email':
            myuser = get_user_model().objects.create_superuser("myuser", "myuser@django-cms.org",
                                                               "myuser@django-cms.org")
        else:
            myuser = get_user_model().objects.create_superuser("myuser", "myuser@django-cms.org", "myuser")

        user = create_page_user(myuser, myuser, grant_all=True)
        puf = PageUserForm(instance=user)
        names = ['can_add_page', 'can_change_page', 'can_delete_page',
                 'can_add_pageuser', 'can_change_pageuser',
                 'can_delete_pageuser', 'can_add_pagepermission',
                 'can_change_pagepermission', 'can_delete_pagepermission']
        for name in names:
            self.assertTrue(puf.initial.get(name, False))


class PermissionFormTestCase(CMSTestCase):
    def test_permission_forms(self):
        page = create_page("page_b", "nav_playground.html", "en",
                           created_by=self.get_superuser())
        normal_user = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        assign_user_to_page(page, normal_user, can_view=True,
                            can_change=True)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(URL_CMS_PAGE_PERMISSION_CHANGE % page.pk)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(URL_CMS_PAGE_PERMISSIONS % page.pk)
            self.assertEqual(response.status_code, 200)

        with self.settings(CMS_RAW_ID_USERS=True):
            data = {
                'page': page.pk,
                'grant_on': "hello",
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertFalse(form.is_valid())
            data = {
                'page': page.pk,
                'grant_on': ACCESS_PAGE,
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertTrue(form.is_valid())
            form.save()

            data = {
                'page': page.pk,
                'grant_on': ACCESS_PAGE_AND_CHILDREN,
                'can_add': '1',
                'can_change': ''
            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertFalse(form.is_valid())
            self.assertTrue('<li>Add page permission also requires edit page '
                            'permission.</li>' in str(form.errors))
            data = {
                'page': page.pk,
                'grant_on': ACCESS_PAGE,
                'can_add': '1',

            }
            form = PagePermissionInlineAdminForm(data=data, files=None)
            self.assertFalse(form.is_valid())
            self.assertTrue('<li>Add page permission requires also access to children, or '
                            'descendants, otherwise added page can&#39;t be changed by its '
                            'creator.</li>' in str(form.errors))

    def test_inlines(self):
        user = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        page = create_page("page_b", "nav_playground.html", "en",
                           created_by=self.get_superuser())
        data = {
            'page': page.pk,
            'grant_on': ACCESS_PAGE_AND_CHILDREN,
            'can_view': 'True',
            'user': '',
            'group': '',
        }
        set_current_user(self.get_superuser())
        form = ViewRestrictionInlineAdminForm(data=data, files=None)
        self.assertTrue(form.is_valid())
        data = {
            'page': page.pk,
            'grant_on': ACCESS_PAGE_AND_CHILDREN,
            'can_view': 'True',
            'user': '',
            'group': ''
        }
        form = GlobalPagePermissionAdminForm(data=data, files=None)
        self.assertFalse(form.is_valid())

        data = {
            'page': page.pk,
            'grant_on': ACCESS_PAGE_AND_CHILDREN,
            'can_view': 'True',
            'user': user.pk,

        }
        form = GlobalPagePermissionAdminForm(data=data, files=None)
        self.assertTrue(form.is_valid())

    def test_user_forms(self):
        user = self.get_superuser()
        user2 = self._create_user("randomuser", is_staff=True, add_default_permissions=True)
        set_current_user(user)
        data = {'username': "test",
                'password': 'hello',
                'password1': 'hello',
                'password2': 'hello',
                'created_by': user.pk,
                'last_login': datetime.now(),
                'date_joined': datetime.now(),
                'email': 'test@example.com',
        }

        form = PageUserForm(data=data, files=None)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        data = {'username': "test2",
                'password': 'hello',
                'password1': 'hello',
                'password2': 'hello',
                'email': 'test2@example.com',
                'created_by': user.pk,
                'last_login': datetime.now(),
                'date_joined': datetime.now(),
                'notify_user': 'on',
        }
        form = PageUserForm(data=data, files=None, instance=user2)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        data = {
            'name': 'test_group'
        }
        form = PageUserGroupForm(data=data, files=None)
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        form = PageUserGroupForm(data=data, files=None, instance=instance)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
