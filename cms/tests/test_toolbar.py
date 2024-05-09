import datetime
import re
from unittest.mock import patch

import iptools
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import truncatewords
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.functional import lazy
from django.utils.html import escape
from django.utils.translation import get_language, gettext_lazy as _, override

from cms.admin.forms import RequestToolbarForm
from cms.api import add_plugin, create_page, create_page_content
from cms.cms_toolbars import (
    ADMIN_MENU_IDENTIFIER,
    ADMINISTRATION_BREAK,
    LANGUAGE_MENU_IDENTIFIER,
    get_user_model,
)
from cms.models import PagePermission, UserSettings
from cms.test_utils.project.placeholderapp.models import (
    CharPksExample,
    Example1,
)
from cms.test_utils.project.placeholderapp.views import (
    ClassDetail,
    detail_view,
)
from cms.test_utils.testcases import URL_CMS_USERSETTINGS, CMSTestCase
from cms.test_utils.util.context_managers import UserLoginContext
from cms.toolbar import utils
from cms.toolbar.items import (
    AjaxItem,
    Break,
    ItemSearchResult,
    LinkItem,
    SubMenu,
    ToolbarAPIMixin,
)
from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar.utils import (
    add_live_url_querystring_param,
    get_object_edit_url,
    get_object_for_language,
    get_object_preview_url,
    get_object_structure_url,
)
from cms.toolbar_pool import toolbar_pool
from cms.utils.compat import DJANGO_4_2
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_tuple
from cms.utils.urlutils import admin_reverse
from cms.views import details


class ToolbarTestBase(CMSTestCase):

    def get_anon(self):
        return AnonymousUser()

    def get_staff(self):
        staff = self._create_user('staff', True, False)
        staff.user_permissions.add(Permission.objects.get(codename='change_page'))
        return staff

    def get_nonstaff(self):
        nonstaff = self._create_user('nonstaff')
        nonstaff.user_permissions.add(Permission.objects.get(codename='change_page'))
        return nonstaff

    def get_superuser(self):
        superuser = self._create_user('superuser', True, True)
        return superuser

    def _get_example_obj(self):
        obj = Example1.objects.create(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        obj.save()
        return obj


@override_settings(ROOT_URLCONF='cms.test_utils.project.nonroot_urls')
class ToolbarMiddlewareTest(ToolbarTestBase):

    @override_settings(CMS_TOOLBAR_HIDE=False)
    def test_no_app_setted_show_toolbar_in_non_cms_urls(self):
        request = self.get_page_request(None, self.get_anon(), '/en/example/')
        self.assertTrue(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=False)
    def test_no_app_setted_show_toolbar_in_cms_urls(self):
        page = create_page('foo', 'col_two.html', 'en')
        request = self.get_page_request(page, self.get_anon())
        self.assertTrue(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=False)
    def test_app_setted_hide_toolbar_in_non_cms_urls_toolbar_hide_unsetted(self):
        request = self.get_page_request(None, self.get_anon(), '/en/example/')
        self.assertTrue(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=True)
    def test_app_setted_hide_toolbar_in_non_cms_urls(self):
        request = self.get_page_request(None, self.get_anon(), '/en/example/')
        self.assertFalse(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=False)
    def test_app_setted_show_toolbar_in_cms_urls(self):
        page = create_page('foo', 'col_two.html', 'en')
        page = create_page('foo', 'col_two.html', 'en', parent=page)
        request = self.get_page_request(page, self.get_anon())
        self.assertTrue(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=True)
    def test_app_setted_show_toolbar_in_cms_urls_subpage(self):
        page = create_page('foo', 'col_two.html', 'en')
        page = create_page('foo', 'col_two.html', 'en', parent=page)
        request = self.get_page_request(page, self.get_anon())
        self.assertTrue(hasattr(request, 'toolbar'))

    def test_cms_internal_ips_unset(self):
        with self.settings(CMS_INTERNAL_IPS=[]):
            request = self.get_page_request(None, self.get_staff(), '/en/example/')
            self.assertTrue(hasattr(request, 'toolbar'))

    def test_cms_internal_ips_set_no_match(self):
        with self.settings(CMS_INTERNAL_IPS=['123.45.67.89', ]):
            request = self.get_page_request(None, self.get_staff(), '/en/example/')
            self.assertFalse(hasattr(request, 'toolbar'))

    def test_cms_internal_ips_set_match(self):
        with self.settings(CMS_INTERNAL_IPS=['127.0.0.0', '127.0.0.1', '127.0.0.2', ]):
            request = self.get_page_request(None, self.get_staff(), '/en/example/')
            self.assertTrue(hasattr(request, 'toolbar'))

    def test_cms_internal_ips_iptools(self):
        with self.settings(CMS_INTERNAL_IPS=iptools.IpRangeList(('127.0.0.0', '127.0.0.255'))):
            request = self.get_page_request(None, self.get_staff(), '/en/example/')
            self.assertTrue(hasattr(request, 'toolbar'))

    def test_cms_internal_ips_iptools_bad_range(self):
        with self.settings(CMS_INTERNAL_IPS=iptools.IpRangeList(('128.0.0.0', '128.0.0.255'))):
            request = self.get_page_request(None, self.get_staff(), '/en/example/')
            self.assertFalse(hasattr(request, 'toolbar'))


@override_settings(CMS_PERMISSION=False)
class ToolbarTests(ToolbarTestBase):

    def get_page_item(self, toolbar):
        items = toolbar.get_left_items() + toolbar.get_right_items()
        page_item = [item for item in items if force_str(getattr(item, "name", None)) == 'Page']
        self.assertEqual(len(page_item), 1)
        return page_item[0]

    def test_toolbar_login(self):
        admin = self.get_superuser()
        endpoint = reverse('cms_login') + '?next=/en/admin/'
        username = getattr(admin, get_user_model().USERNAME_FIELD)
        password = getattr(admin, get_user_model().USERNAME_FIELD)
        response = self.client.post(endpoint, data={'username': username, 'password': password})
        self.assertRedirects(response, '/en/admin/')
        self.assertTrue(settings.SESSION_COOKIE_NAME in response.cookies)

    def test_toolbar_login_error(self):
        admin = self.get_superuser()
        endpoint = reverse('cms_login') + '?next=/en/admin/'
        username = getattr(admin, get_user_model().USERNAME_FIELD)
        response = self.client.post(endpoint, data={'username': username, 'password': 'invalid'})
        self.assertRedirects(response, '/en/admin/?cms_toolbar_login_error=1', target_status_code=302)
        self.assertFalse(settings.SESSION_COOKIE_NAME in response.cookies)

    def test_toolbar_login_invalid_redirect_to(self):
        admin = self.get_superuser()
        endpoint = reverse('cms_login') + '?next=http://example.com'
        username = getattr(admin, get_user_model().USERNAME_FIELD)
        password = getattr(admin, get_user_model().USERNAME_FIELD)
        response = self.client.post(endpoint, data={'username': username, 'password': password})
        self.assertRedirects(response, '/en/')
        self.assertTrue(settings.SESSION_COOKIE_NAME in response.cookies)

    @override_settings(CMS_TOOLBARS=['cms.test_utils.project.sampleapp.cms_toolbars.ToolbarWithMedia'])
    def test_toolbar_media(self):
        """
        Toolbar classes can declare a media class or property
        to be rendered along with the toolbar.
        """
        old_pool = toolbar_pool.toolbars
        toolbar_pool.clear()
        cms_page = create_page("toolbar-page", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(cms_page)
        endpoint = get_object_edit_url(page_content)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(endpoint)

        self.assertContains(response, 'src="/static/samplemap/js/sampleapp.js"')
        self.assertContains(response, 'href="/static/samplemap/css/sampleapp.css"')

        toolbar_pool.toolbars = old_pool
        toolbar_pool._discovered = True

    def test_toolbar_request_endpoint_validation(self):
        endpoint = self.get_admin_url(UserSettings, 'get_toolbar')
        cms_page = create_page("toolbar-page", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(cms_page)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(
                endpoint,
                data={
                    'obj_id': page_content.pk,
                    'obj_type': 'cms.pagecontent',
                    'cms_path': get_object_edit_url(page_content)
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Clipboard")

            response = self.client.get(
                endpoint,
                data={
                    'obj_id': page_content.pk,
                    'obj_type': 'cms.pagecontent',
                    'cms_path': get_object_edit_url(page_content) + "q"  # Invalid
                },
            )
            self.assertEqual(response.status_code, 200)
            # No clipboard exposed to invalid cms_path
            self.assertNotContains(response, "Clipboard")

            # Invalid app / model
            response = self.client.get(
                endpoint,
                data={
                    'obj_id': cms_page.pk,
                    'obj_type': 'cms.somemodel',
                    'cms_path': cms_page.get_absolute_url('en')
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_toolbar_request_form(self):
        cms_page = create_page("toolbar-page", "col_two.html", "en")
        generic_obj = self._get_example_obj()

        # Valid forms
        form = RequestToolbarForm({
            'obj_id': cms_page.pk,
            'obj_type': 'cms.page',
            'cms_path': cms_page.get_absolute_url('en'),
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['attached_obj'], cms_page)

        form = RequestToolbarForm({
            'obj_id': generic_obj.pk,
            'obj_type': 'placeholderapp.example1',
            'cms_path': cms_page.get_absolute_url('en'),
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['attached_obj'], generic_obj)

        # Invalid forms
        form = RequestToolbarForm({
            'obj_id': 1000,
            'obj_type': 'cms.page',
            'cms_path': cms_page.get_absolute_url('en'),
        })
        self.assertFalse(form.is_valid())

        form = RequestToolbarForm({
            'obj_id': cms_page.pk,
            'obj_type': 'cms.somemodel',
            'cms_path': cms_page.get_absolute_url('en'),
        })
        self.assertFalse(form.is_valid())

        form = RequestToolbarForm({
            'obj_id': cms_page.pk,
            'obj_type': 'cms.page',
            'cms_path': 'https://example.com/some-path/',
        })
        self.assertFalse(form.is_valid())

    def test_no_page_anon(self):
        request = self.get_page_request(None, self.get_anon(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 0)

    def test_no_page_staff(self):
        request = self.get_page_request(None, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + admin-menu + color scheme + logout
        self.assertEqual(len(items), 4, items)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 12, admin_items)

    def test_no_page_superuser(self):
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + admin-menu + color scheme + logout
        self.assertEqual(len(items), 4)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 13, admin_items)

    def test_anon(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.get_page_request(page, self.get_anon())
        toolbar = CMSToolbar(request)

        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 0)

    def test_nonstaff(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.get_page_request(page, self.get_nonstaff())
        toolbar = CMSToolbar(request)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + logout
        self.assertEqual(len(items), 0)

    @override_settings(CMS_PERMISSION=True)
    def test_template_change_permission(self):
        page = create_page('test', 'nav_playground.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)

        # Staff user with change page permissions only
        staff_user = self.get_staff_user_with_no_permissions()
        self.add_permission(staff_user, 'change_page')
        global_permission = self.add_global_permission(staff_user, can_change=True, can_delete=True)

        # User should not see "Templates" option because he only has
        # "change" permission.
        request = self.get_page_request(page, staff_user, edit_url)
        toolbar = CMSToolbar(request)
        page_item = self.get_page_item(toolbar)
        template_item = [
            item for item in page_item.items
            if force_str(getattr(item, 'name', '')) == 'Templates'
        ]
        self.assertEqual(len(template_item), 0)

        # Give the user change advanced settings permission
        global_permission.can_change_advanced_settings = True
        global_permission.save()

        # Reload user to avoid stale caches
        staff_user = self.reload(staff_user)

        # User should see "Templates" option because
        # he has "change advanced settings" permission
        request = self.get_page_request(page, staff_user, edit_url)
        toolbar = CMSToolbar(request)
        page_item = self.get_page_item(toolbar)
        template_item = [
            item for item in page_item.items
            if force_str(getattr(item, 'name', '')) == 'Templates'
        ]
        self.assertEqual(len(template_item), 1)

    def test_markup(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_edit_url = get_object_edit_url(page_content)
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            response = self.client.get(page_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'nav_playground.html')
        self.assertContains(response, '<div id="cms-top"')
        self.assertContains(response, 'cms.base.css')

    def test_placeholder_buttons_on_app_page(self):
        """
        Checks that the "edit page" button shows up
        on non-cms pages with app placeholders.
        """
        superuser = self.get_superuser()
        ex1 = self._get_example_obj()

        # Test for Edit button
        obj_edit_url = get_object_edit_url(ex1)

        with self.login_user_context(superuser):
            response = self.client.get('/en/example/latest/')
        self.assertEqual(response.status_code, 200)
        toolbar = response.wsgi_request.toolbar
        self.assertEqual(len(toolbar.get_right_items()[2].buttons), 1)
        edit_button = toolbar.get_right_items()[2].buttons[0]
        self.assertEqual(edit_button.name, 'Edit')
        self.assertEqual(edit_button.url, obj_edit_url)
        self.assertEqual(
            edit_button.extra_classes,
            ['cms-btn', 'cms-btn-action', 'cms-btn-switch-edit']
        )

        # Test for Preview button
        obj_preview_url = get_object_preview_url(ex1)

        with self.login_user_context(superuser):
            response = self.client.get(obj_edit_url)
        self.assertEqual(response.status_code, 200)
        toolbar = response.wsgi_request.toolbar
        self.assertEqual(len(toolbar.get_right_items()[2].buttons), 1)
        preview_button = toolbar.get_right_items()[2].buttons[0]
        self.assertEqual(preview_button.name, 'Preview')
        self.assertEqual(preview_button.url, obj_preview_url)
        self.assertEqual(
            preview_button.extra_classes,
            ['cms-btn', 'cms-btn-switch-save']
        )

    def test_markup_generic_module(self):
        page = create_page("toolbar-page", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_structure_url = get_object_structure_url(page_content)
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            response = self.client.get(page_structure_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="cms-submenu-item cms-submenu-item-title"><span>Generic</span>')

    def test_markup_link_custom_module(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_structure_url = get_object_structure_url(page_content)

        with self.login_user_context(superuser):
            response = self.client.get(page_structure_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="LinkPlugin">')
        self.assertContains(
            response,
            '<div class="cms-submenu-item cms-submenu-item-title"><span>Different Grouper</span>'
        )

    def test_placeholder_menu_items(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_structure_url = get_object_structure_url(page_content)
        placeholders = page_content.get_placeholders()
        self.assertEqual(len(placeholders), 2)  # we get two placeholders

        with self.login_user_context(superuser):
            response = self.client.get(page_structure_url)

        self.assertEqual(response.status_code, 200)
        expected_bits = (
            # Copy all in placeholder menu
            '<div class="cms-submenu-item"><a data-cms-icon="copy" data-rel="copy" href="#">Copy all</a></div>',
            # Past in placeholder menu
            '<div class="cms-submenu-item"><a data-cms-icon="paste" data-rel="paste" href="#">Paste</a></div>',
            # Empty all placeholder menu (for both placeholders)
            '<div class="cms-submenu-item"><a data-cms-icon="bin" data-rel="modal" href="'
            + reverse("admin:cms_placeholder_clear_placeholder", args=(placeholders[0].id, )),
            '<div class="cms-submenu-item"><a data-cms-icon="bin" data-rel="modal" href="'
            + reverse("admin:cms_placeholder_clear_placeholder", args=(placeholders[1].id, )),
            'data-name="sidebar column">Empty all</a></div>',
            # Extra items in placeholder menu
            '<div class="cms-submenu-item"><a href="/some/url/" data-rel="ajax"',
            'data-on-success="REFRESH_PAGE" data-cms-icon="whatever" >Data item - not usable</a></div>',
            '<div class="cms-submenu-item"><a href="/some/other/url/" data-rel="ajax_add"',
        )
        for bit in expected_bits:
            self.assertContains(response, bit)

    def test_markup_plugin_template(self):
        page = create_page("toolbar-page-1", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_edit_url = get_object_edit_url(page_content)
        plugin_1 = add_plugin(
            page.get_placeholders("en").get(slot='col_left'), language='en',
            plugin_type='TestPluginAlpha', alpha='alpha'
        )
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_url)
        self.assertEqual(response.status_code, 200)
        response_text = response.render().rendered_content
        self.assertTrue(
            re.search('edit_plugin.+/en/admin/cms/placeholder/edit-plugin/%s' % plugin_1.pk, response_text)
        )
        self.assertTrue(re.search('move_plugin.+/en/admin/cms/placeholder/move-plugin/', response_text))
        self.assertTrue(
            re.search('delete_plugin.+/en/admin/cms/placeholder/delete-plugin/%s/' % plugin_1.pk, response_text)
        )
        self.assertTrue(re.search('add_plugin.+/en/admin/cms/placeholder/add-plugin/', response_text))
        self.assertTrue(re.search('copy_plugin.+/en/admin/cms/placeholder/copy-plugins/', response_text))

    def test_show_toolbar_to_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        staff = self.get_staff()
        assert staff.user_permissions.get().name == 'Can change page'
        request = self.get_page_request(page, staff, '/')
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_remove_and_copy_urls_are_correctly_associated_with_pagecontent(self):
        """
        The urls to copy and remove translations should be linked correctly.
        """
        def get_delete_url(pk):
            return admin_reverse('cms_pagecontent_delete', args=(pk,))

        page = create_page("english-page", "nav_playground.html", "en")
        german_content = create_page_content("de", "german content", page)
        english_content = page.get_content_obj('en')
        edit_url = get_object_edit_url(english_content)
        staff = self.get_staff()
        self.client.force_login(staff)

        response = self.client.get(edit_url)
        menus = response.context['cms_toolbar'].menus
        language_menu = menus['language-menu']
        delete = language_menu.items[-2]
        german_delete = delete.items[0]
        english_delete = delete.items[1]

        copy = language_menu.items[-1]
        copy_german = copy.items[0]
        copy_german_context = copy_german.get_context()

        self.assertEqual(delete.name.lower(), 'delete translation')
        self.assertEqual(german_delete.name.lower(), 'german...')
        self.assertEqual(german_delete.url.split('?')[0], get_delete_url(german_content.pk))

        self.assertEqual(english_delete.name.lower(), 'english...')
        self.assertEqual(english_delete.url.split('?')[0], get_delete_url(english_content.pk))

        self.assertEqual(copy_german.name.lower(), 'from german')
        self.assertEqual(
            copy_german_context['action'],
            admin_reverse('cms_pagecontent_copy_language', args=(german_content.pk,))
        )

    def test_show_toolbar_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        request = self.get_page_request(page, self.get_staff(), edit_url)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_hide_toolbar_non_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        request = self.get_page_request(page, self.get_nonstaff(), edit_url)
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_hide_toolbar_disabled(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        # Edit mode should re-enable the toolbar in any case
        request = self.get_page_request(page, self.get_staff(), disable=True)
        self.assertTrue(request.session.get('cms_toolbar_disabled'))
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.edit_mode_active)

    def test_show_disabled_toolbar_with_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        request = self.get_page_request(page, self.get_staff(), edit_url, disable=True)
        self.assertFalse(request.session.get('cms_toolbar_disabled'))
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_hide_toolbar_disabled_no_persist(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        request = self.get_page_request(page, self.get_staff(), disable=True, persist=False)
        self.assertFalse(request.session.get('cms_toolbar_disabled'))
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_toolbar_login_redirect_validation(self):
        user = self._create_user('toolbar', True, True)
        username = getattr(user, user.USERNAME_FIELD)
        page = create_page("toolbar-page", "nav_playground.html", "en")
        page.set_as_homepage()
        login_url = reverse('cms_login')
        endpoint = f'{login_url}?next=https://notyourdomain.com'
        response = self.client.post(endpoint, {'username': username, 'password': username})
        self.assertRedirects(response, page.get_absolute_url(), fetch_redirect_response=False)

    @override_settings(CMS_TOOLBAR_ANONYMOUS_ON=True)
    def test_show_toolbar_login_anonymous(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        page_url = "%s?%s" % (page.get_absolute_url(), get_cms_setting('TOOLBAR_URL__ENABLE'))
        response = self.client.get(page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cms-toolbar')

    @override_settings(CMS_TOOLBAR_ANONYMOUS_ON=False)
    def test_hide_toolbar_login_anonymous_setting(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        response = self.client.get(page.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'cms-toolbar')

    def test_admin_logout_staff(self):
        with override_settings(CMS_PERMISSION=True):
            with self.login_user_context(self.get_staff()):
                response = self.client.post('/en/admin/logout/')
                self.assertTrue(response.status_code, 200)

    def test_show_toolbar_without_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        request = self.get_page_request(page, AnonymousUser())
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_no_change_button(self):
        page = create_page('test', 'nav_playground.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        user = self.get_staff()
        user.user_permissions.all().delete()
        request = self.get_page_request(page, user, edit_url, disable=False)
        request.toolbar.post_template_populate()
        self.assertFalse(page.has_change_permission(request.user))

        items = request.toolbar.get_left_items() + request.toolbar.get_right_items()
        # Logo + page-menu + admin-menu + color scheme + logout
        self.assertEqual(len(items), 5, items)
        page_items = items[1].get_items()
        # The page menu should only have the "Create page" item enabled.
        self.assertFalse(page_items[0].disabled)
        self.assertTrue(all(item.disabled for item in page_items[1:] if hasattr(item, 'disabled')))
        admin_items = request.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 14, admin_items)

    def test_button_consistency_staff(self):
        """
        Tests that the buttons remain even when the language changes.
        """
        user = self.get_staff()
        cms_page = create_page('test-en', 'nav_playground.html', 'en')
        page_content_en = self.get_pagecontent_obj(cms_page)
        edit_url_en = get_object_edit_url(page_content_en)
        page_content_de = create_page_content('de', 'test-de', cms_page)
        edit_url_de = get_object_edit_url(page_content_de)

        en_request = self.get_page_request(cms_page, user, edit_url_en)
        en_toolbar = CMSToolbar(en_request)
        en_toolbar.set_object(page_content_en)
        en_toolbar.populate()
        en_toolbar.post_template_populate()
        # Logo + templates + page-menu + admin-menu + color scheme + logout
        self.assertEqual(len(en_toolbar.get_left_items() + en_toolbar.get_right_items()), 6)
        de_request = self.get_page_request(cms_page, user, edit_url_de, lang_code='de')
        de_toolbar = CMSToolbar(de_request)
        de_toolbar.set_object(page_content_de)
        de_toolbar.populate()
        de_toolbar.post_template_populate()
        # Logo + templates + page-menu + admin-menu + color scheme + logout
        self.assertEqual(len(de_toolbar.get_left_items() + de_toolbar.get_right_items()), 6)

    def test_double_menus(self):
        """
        Tests that even called multiple times, admin and language buttons are not duplicated
        """
        user = self.get_staff()
        page = create_page('test', 'nav_playground.html', 'en')
        for code, verbose in get_language_tuple():
            if code != "en":
                create_page_content(code, f"test {code}", page)
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        en_request = self.get_page_request(None, user, edit_url)
        toolbar = CMSToolbar(en_request)
        toolbar.set_object(page_content)
        toolbar.populated = False
        toolbar.populate()
        toolbar.populated = False
        toolbar.populate()
        toolbar.populated = False
        toolbar.post_template_populate()
        get_object_for_language(page_content, "de")
        admin = toolbar.get_left_items()[0]
        lang = toolbar.get_left_items()[1]
        self.assertEqual(len(admin.get_items()), 15)
        self.assertEqual(len(lang.get_items()), len(get_language_tuple(1)))
        self.assertIn(edit_url, [item.url for item in lang.get_items()])  # Edit urls returned

    @override_settings(CMS_PLACEHOLDER_CONF={'col_left': {'name': 'PPPP'}})
    def test_placeholder_name(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "col_two.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_edit_url = get_object_edit_url(page_content)

        with self.login_user_context(superuser):
            response = self.client.get(page_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PPPP')

    def test_user_settings(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(URL_CMS_USERSETTINGS)
            self.assertEqual(response.status_code, 200)

    def test_remove_lang(self):
        page = create_page('test', 'nav_playground.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        page_edit_url = get_object_edit_url(page_content)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_url)
            self.assertEqual(response.status_code, 200)
            setting = UserSettings.objects.get(user=superuser)
            setting.language = 'it'
            setting.save()
            with self.settings(LANGUAGES=(('en', 'english'),)):
                response = self.client.get(page_edit_url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, '/it/')

    def test_get_alphabetical_insert_position(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        toolbar.get_left_items()
        toolbar.get_right_items()

        admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'TestAppMenu')

        # Insert alpha
        alpha_position = admin_menu.get_alphabetical_insert_position('menu-alpha', SubMenu, None)

        # As this will be the first item added to this, this use should return the default, or namely None
        if not alpha_position:
            alpha_position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK) + 1
        admin_menu.get_or_create_menu('menu-alpha', 'menu-alpha', position=alpha_position)

        # Insert gamma (should return alpha_position + 1)
        gamma_position = admin_menu.get_alphabetical_insert_position('menu-gamma', SubMenu)
        self.assertEqual(int(gamma_position), int(alpha_position) + 1)
        admin_menu.get_or_create_menu('menu-gamma', 'menu-gamma', position=gamma_position)

        # Where should beta go? It should go right where gamma is now...
        beta_position = admin_menu.get_alphabetical_insert_position('menu-beta', SubMenu)
        self.assertEqual(beta_position, gamma_position)

    def test_out_of_order(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        menu1 = toolbar.get_or_create_menu("test")
        menu2 = toolbar.get_or_create_menu("test", "Test", side=toolbar.RIGHT, position=2)

        self.assertEqual(menu1, menu2)
        self.assertEqual(menu1.name, 'Test')
        self.assertEqual(len(toolbar.get_right_items()), 2)  # Including color scheme switch

    def test_negative_position_left(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        # Starting point: [Menu:Example, Menu:Page, Menu:Language]
        # Example @ 1, Page @ 2, Language @ -1
        menu1 = toolbar.get_or_create_menu("menu1", "Menu1", side=toolbar.LEFT, position=-2)
        menu2 = toolbar.get_or_create_menu("menu2", "Menu2", side=toolbar.LEFT, position=-3)
        self.assertEqual(toolbar.get_left_items().index(menu1), 3)
        self.assertEqual(toolbar.get_left_items().index(menu2), 2)

    def test_negative_position_right(self):
        page = create_page("toolbar-page", "nav_playground.html", "en")
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        # Starting point: [] (empty)
        # Add a couple of "normal" menus
        toolbar.get_or_create_menu("menu1", "Menu1", side=toolbar.RIGHT)
        toolbar.get_or_create_menu("menu2", "Menu2", side=toolbar.RIGHT)
        menu3 = toolbar.get_or_create_menu("menu3", "Menu3", side=toolbar.RIGHT, position=-1)
        menu4 = toolbar.get_or_create_menu("menu4", "Menu4", side=toolbar.RIGHT, position=-2)
        self.assertEqual(toolbar.get_right_items().index(menu3), 4)  # Including color scheme
        self.assertEqual(toolbar.get_right_items().index(menu4), 3)  # Including color scheme

    def assertMenuItems(self, request, menu_id, name, items=None):
        toolbar = CMSToolbar(request)
        toolbar.populate()
        menu = dict(
            (force_str(getattr(item, 'name', '|')), item)
            for item in toolbar.get_menu(menu_id).get_items()
        )
        self.assertIn(name, list(menu))
        if items is not None:
            sub_menu = list(
                force_str(getattr(item, 'name', '|')) for item in menu[name].get_items()
            )
            self.assertEqual(sorted(sub_menu), sorted(items))

    def test_remove_language(self):
        page = create_page(
            "toolbar-page", "nav_playground.html", "en"
        )
        create_page_content(title="de page", language="de", page=page)
        create_page_content(title="fr page", language="fr", page=page)
        page_content_en = self.get_pagecontent_obj(page)
        edit_url_en = get_object_edit_url(page_content_en)
        request = self.get_page_request(page, self.get_staff(), edit_url_en)

        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Delete Translation',
            ['German...', 'English...', 'French...']
        )

        reduced_langs = {
            1: [
                {
                    'code': 'en',
                    'name': 'English',
                    'fallbacks': ['fr', 'de'],
                    'public': True,
                },
                {
                    'code': 'fr',
                    'name': 'French',
                    'public': True,
                },
            ]
        }

        with self.settings(CMS_LANGUAGES=reduced_langs):
            self.assertMenuItems(
                request, LANGUAGE_MENU_IDENTIFIER, 'Delete Translation',
                ['English...', 'French...']
            )

    def test_add_language(self):
        page = create_page("tbp", "nav_playground.html", "en")
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        request = self.get_page_request(page, self.get_staff(), edit_url)
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Add Translation',
            ['German...', 'Brazilian Portuguese...', 'French...', 'Espa\xf1ol...']
        )

        create_page_content(title="de page", language="de", page=page)
        create_page_content(title="fr page", language="fr", page=page)
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Add Translation',
            ['Brazilian Portuguese...', 'Espa\xf1ol...']
        )

    def test_copy_plugins(self):
        page = create_page("tbp", "nav_playground.html", "en")
        title_en = self.get_pagecontent_obj(page)
        edit_url_en = get_object_edit_url(title_en)
        title_de = create_page_content('de', 'de page', page, template='nav_playground.html')
        edit_url_de = get_object_edit_url(title_de)
        add_plugin(title_de.placeholders.get(slot='body'), "TextPlugin", "de", body='de body')
        title_fr = create_page_content('fr', 'fr page', page, template='nav_playground.html')
        add_plugin(title_fr.placeholders.get(slot='body'), "TextPlugin", "fr", body='fr body')

        staff = self.get_staff()

        request = self.get_page_request(page, staff, edit_url_en)
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, _('Copy all plugins'),
            ['from German', 'from French']
        )

        request = self.get_page_request(page, staff, edit_url_de, lang_code='de')
        request.toolbar.toolbar_language = "en"
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, _('Copy all plugins'),
            ['from English', 'from French', ]
        )

    def get_username(self, user=None, default=''):
        user = user or self.request.user
        try:
            name = user.get_full_name()
            if name:
                return name
            else:
                return user.get_username()
        except (AttributeError, NotImplementedError):
            return default

    def test_toolbar_logout(self):
        '''
        Tests that the Logout menu item includes the user's full name, if the
        relevant fields were populated in auth.User, else the user's username.
        '''
        superuser = self.get_superuser()

        # Ensure that some other test hasn't set the name fields
        if superuser.get_full_name():
            # Looks like it has been set, clear them
            superuser.first_name = ''
            superuser.last_name = ''
            superuser.save()

        page = create_page("home", "nav_playground.html", "en")
        page_content = self.get_pagecontent_obj(page)
        page_edit_url = get_object_edit_url(page_content)
        self.get_page_request(page, superuser, '/')
        #
        # Test that the logout shows the username of the logged-in user if
        # first_name and last_name haven't been provided.
        #
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_url)
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertTrue(admin_menu.find_first(AjaxItem, name=_('Logout %s') % self.get_username(superuser)))

        #
        # Test that the logout shows the logged-in user's name, if it was
        # populated in auth.User.
        #
        superuser.first_name = 'Super'
        superuser.last_name = 'User'
        superuser.save()
        # Sanity check...
        self.get_page_request(page, superuser, '/')
        page_content = self.get_pagecontent_obj(page)
        page_edit_url = get_object_edit_url(page_content)
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_url)
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertTrue(admin_menu.find_first(AjaxItem, name=_('Logout %s') % self.get_username(superuser)))

    @override_settings(CMS_PERMISSION=True)
    def test_toolbar_logout_redirect(self):
        """
        Tests the logount AjaxItem on_success parameter in four different conditions:
         * published page: no redirect
         * unpublished page: redirect to the home page
         * published page with login_required: redirect to the home page
         * published page with view permissions: redirect to the home page
        """
        superuser = self.get_superuser()
        page0 = create_page("home", "nav_playground.html", "en")
        page1 = create_page("internal", "nav_playground.html", "en",
                            parent=page0)
        page1_content = self.get_pagecontent_obj(page1)
        page1_edit_url = get_object_edit_url(page1_content)
        create_page("unpublished", "nav_playground.html", "en", parent=page0)
        page3 = create_page("login_restricted", "nav_playground.html", "en",
                            parent=page0, login_required=True)
        page3_content = self.get_pagecontent_obj(page3)
        page3_edit_url = get_object_edit_url(page3_content)
        page4 = create_page("view_restricted", "nav_playground.html", "en",
                            parent=page0)
        page4_content = self.get_pagecontent_obj(page4)
        page4_edit_url = get_object_edit_url(page4_content)
        PagePermission.objects.create(page=page4, can_view=True,
                                      user=superuser)
        self.get_page_request(page4, superuser, '/')

        with self.login_user_context(superuser):
            # Published page, no redirect
            response = self.client.get(page1_edit_url)
            toolbar = response.context['request'].toolbar
            menu_name = _('Logout %s') % self.get_username(superuser)
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertTrue(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success)

            # Published page with login restrictions, redirect
            response = self.client.get(page3_edit_url)
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertEqual(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success, '/')

            # Published page with view permissions, redirect
            response = self.client.get(page4_edit_url)
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertEqual(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success, '/')


@override_settings(ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls')
class EditModelTemplateTagTest(ToolbarTestBase):
    edit_fields_rx = "(\\?|&amp;)edit_fields=%s"

    def tearDown(self):
        Example1.objects.all().delete()
        super().tearDown()

    def test_markup_toolbar_url_model(self):
        superuser = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        preview_url = get_object_preview_url(page_content)
        ex1 = self._get_example_obj()
        # object
        # check when in draft mode
        request = self.get_page_request(page, superuser, edit_url)
        response = detail_view(request, ex1.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s"' % get_object_preview_url(ex1))
        # check when in live mode
        request = self.get_page_request(page, superuser, preview_url)
        response = detail_view(request, ex1.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s"' % get_object_edit_url(ex1))

    def test_anon(self):
        user = self.get_anon()
        page = create_page('Test', 'col_two.html', 'en')
        ex1 = self._get_example_obj()
        request = self.get_page_request(page, user)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, "<h1>one</h1>")
        self.assertNotContains(response, "CMS.API")

    def test_noedit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        ex1 = self._get_example_obj()
        request = self.get_page_request(page, user)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, "<h1>one</h1>")
        self.assertContains(response, "CMS.API")

    def test_edit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()

        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk)
        self.assertContains(
            response,
            '<h1><template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model">'
            '</template></h1>'.format(
                'placeholderapp', 'example1', 'char_1', ex1.pk
            )
        )

    def test_invalid_item(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model fake "char_1" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-%s cms-render-model"></template>' % ex1.pk)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-end cms-plugin-%s cms-render-model"></template>' % ex1.pk)

    def test_as_varname(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" as tempvar %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertNotContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-%s cms-render-model"></template>' % ex1.pk)
        self.assertNotContains(
            response,
            '<template class="cms-plugin cms-plugin-end cms-plugin-%s cms-render-model"></template>' % ex1.pk)

    def test_edit_render_placeholder(self):
        """
        Tests the {% render_placeholder %} templatetag.
        """
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()

        render_placeholder_body = "I'm the render placeholder body"

        plugin = add_plugin(ex1.placeholder, "TextPlugin", "en", body=render_placeholder_body)

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_placeholder instance.placeholder %}</h1>
<h2>{% render_placeholder instance.placeholder as tempvar %}</h2>
<h3>{{ tempvar }}</h3>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            f'<div class="cms-placeholder cms-placeholder-{ex1.placeholder.pk}"></div>')

        self.assertContains(
            response,
            f'<h1><template class="cms-plugin cms-plugin-start cms-plugin-{plugin.pk}"></template>'
            f'{render_placeholder_body}'
            f'<template class="cms-plugin cms-plugin-end cms-plugin-{plugin.pk}"></template>'
        )

        self.assertContains(
            response,
            '<h2></h2>',
        )

        #
        # NOTE: Using the render_placeholder "as" form should /not/ render
        # frontend placeholder editing support.
        #
        self.assertContains(
            response,
            f'<h3>{render_placeholder_body}</h3>'
        )

        self.assertContains(
            response,
            f'CMS._plugins.push(["cms-plugin-{plugin.pk}"'
        )

        self.assertContains(
            response,
            f'CMS._plugins.push(["cms-placeholder-{ex1.placeholder.pk}"'
        )

    def test_filters(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2' %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '{4}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'char_1', ex1.pk, truncatewords(escape(ex1.char_1), 2)))

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" "truncatewords:2|safe" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '{4}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'char_1', ex1.pk, truncatewords(ex1.char_1, 2)))

    def test_setting_override(self):
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2' %}</h1>
{% endblock content %}
'''
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4")
        ex1.save()

        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '{4}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'char_1', ex1.pk, truncatewords(escape(ex1.char_1), 2)))

    def test_filters_date(self):
        # Ensure we have a consistent testing env...
        with self.settings(USE_L10N=False, DATE_FORMAT="M. d, Y"):
            user = self.get_staff()
            page = create_page('Test', 'col_two.html', 'en')
            page_content = self.get_pagecontent_obj(page)
            edit_url = get_object_edit_url(page_content)
            ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>",
                           char_2="char_2",
                           char_3="char_3",
                           char_4="char_4",
                           date_field=datetime.date(2012, 1, 2))
            ex1.save()
            template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" %}</h1>
{% endblock content %}
'''

            request = self.get_page_request(page, user, edit_url)
            response = detail_view(request, ex1.pk, template_string=template_text)
            self.assertContains(
                response,
                '<h1>'
                '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '{4}'
                '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '</h1>'.format(
                    'placeholderapp', 'example1', 'date_field', ex1.pk,
                    ex1.date_field.strftime("%b. %d, %Y" if DJANGO_4_2 else "%b. %-d, %Y")))

            template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" "" "" "safe" %}</h1>
{% endblock content %}
'''
            request = self.get_page_request(page, user, edit_url)
            response = detail_view(request, ex1.pk, template_string=template_text)
            self.assertContains(
                response,
                '<h1>'
                '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '{4}'
                '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '</h1>'.format(
                    'placeholderapp', 'example1', 'date_field', ex1.pk,
                    ex1.date_field.strftime("%Y-%m-%d")))

            template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" "" "" 'date:"Y m d"' %}</h1>
{% endblock content %}
'''
            response = detail_view(request, ex1.pk, template_string=template_text)
            self.assertContains(
                response,
                '<h1>'
                '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '{4}'
                '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '</h1>'.format(
                    'placeholderapp', 'example1', 'date_field', ex1.pk,
                    ex1.date_field.strftime("%Y %m %d")))

    def test_filters_notoolbar(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2' %}</h1>
{% endblock content %}
'''

        request = self.get_page_request(page, user)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<h1>%s</h1>' % truncatewords(escape(ex1.char_1), 2))

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2|safe' "" "" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<h1>%s</h1>' % truncatewords(ex1.char_1, 2))

    def test_no_cms(self):
        user = self.get_staff()
        ex1 = self._get_example_obj()
        edit_url = get_object_edit_url(ex1)
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance %}
{% endblock content %}
'''
        request = self.get_page_request(None, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2} cms-render-model-icon">'
            '</template>'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )
        self.assertContains(response, "onClose: 'REFRESH_PAGE',")

    def test_icon_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2} cms-render-model-icon">'
            '</template>'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )

    def test_icon_followed_by_render_model_block_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance "char_1" %}

{% render_model_block instance "char_2" %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    <span class="date">{{ instance.date_field|date:"Y" }}</span>
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            "CMS._plugins.push(['cms-plugin-{0}-{1}-{2}-{3}'".format('placeholderapp', 'example1', 'char_1', ex1.pk))

        self.assertContains(
            response,
            "CMS._plugins.push(['cms-plugin-{0}-{1}-{2}-{3}'".format('placeholderapp', 'example1', 'char_2', ex1.pk))

    def test_add_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-add-{2} cms-render-model-add">'
            '</template>'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )

    def test_add_tag_class(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance_class %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-add-{2} cms-render-model-add">'
            '</template>'.format(
                'placeholderapp', 'example1', '0'
            )
        )

    def test_add_tag_classview(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance_class %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        view_func = ClassDetail.as_view(template_string=template_text)
        response = view_func(request, pk=ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-add-{2} cms-render-model-add">'
            '</template>'.format(
                'placeholderapp', 'example1', '0'
            )
        )

    def test_block_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4", date_field=datetime.date(2012, 1, 1))
        ex1.save()

        # This template does not render anything as content is saved in a
        # variable and never inserted in the page
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_block instance as rendered_model %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    {{ instance.date_field|date:"Y" }}
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertNotContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'
            '<img src="/static/cms/img/toolbar/render_model_icon.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2} cms-render-model-icon">'
            '</template>'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )

        # This template does not render anything as content is saved in a
        # variable and inserted in the page afterwards
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_block instance as rendered_model %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    <span class="date">{{ instance.date_field|date:"Y" }}</span>
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{{ rendered_model }}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model '
            'cms-render-model-block">'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )
        self.assertContains(response, '<h1>%s - %s</h1>' % (ex1.char_1, ex1.char_2))
        self.assertContains(response, '<span class="date">%s</span>' % (ex1.date_field.strftime("%Y")))
        self.assertContains(
            response, '<a href="%s">successful if</a>\n    \n<template' % (reverse('detail', args=(ex1.pk,)))
        )

        # This template is rendered directly
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_block instance %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    <span class="date">{{ instance.date_field|date:"Y" }}</span>
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model '
            'cms-render-model-block">'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )
        self.assertContains(response, '<h1>%s - %s</h1>' % (ex1.char_1, ex1.char_2))
        self.assertContains(response, '<span class="date">%s</span>' % (ex1.date_field.strftime("%Y")))
        self.assertContains(
            response, '<a href="%s">successful if</a>\n    \n<template' % (reverse('detail', args=(ex1.pk,)))
        )

        # Changelist check
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_block instance 'changelist' %}
    {{ instance }}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-changelist-{2} cms-render-model '
            'cms-render-model-block"></template>'.format(
                'placeholderapp', 'example1', ex1.pk
            )
        )
        self.assertContains(
            response,
            "edit_plugin: '%s?language=%s&amp;edit_fields=changelist'" % (
                admin_reverse('placeholderapp_example1_changelist'), 'en'
            )
        )

    def test_invalid_attribute(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "fake_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model">'
            '</template>'.format(
                'placeholderapp', 'example1', 'fake_field', ex1.pk
            )
        )
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model">'
            '</template>'.format(
                'placeholderapp', 'example1', 'fake_field', ex1.pk
            )
        )

        # no attribute
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            f'<template class="cms-plugin cms-plugin-start cms-plugin-{ex1.pk} cms-render-model"></template>')
        self.assertContains(
            response,
            f'<template class="cms-plugin cms-plugin-end cms-plugin-{ex1.pk} cms-render-model"></template>')

    def test_callable_item(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1><template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model">'
            '</template></h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk
            )
        )

    def test_view_method(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "" "dynamic_url" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response, "edit_plugin: '/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)

    def test_view_url(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response, "edit_plugin: '/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk
        )

    def test_method_attribute(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "" "static_admin_url" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        ex1.set_static_url(request)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk
            )
        )

    def test_admin_url(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        expected_output = (
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'
        ).format('placeholderapp', 'example1', 'callable_item', ex1.pk)
        self.assertContains(response, expected_output)

    def test_admin_url_extra_field(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_2" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk
            )
        )
        self.assertContains(response, "/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_2", response.content.decode('utf8')))

    def test_admin_url_multiple_fields(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk
            )
        )
        self.assertContains(response, "/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_1", response.content.decode('utf8')))
        self.assertTrue(re.search(self.edit_fields_rx % "char_1%2Cchar_2", response.content.decode('utf8')))

    def test_instance_method(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk
            )
        )

    def test_item_from_context(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance item_name %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit_url)
        response = detail_view(request, ex1.pk, template_string=template_text,
                               item_name="callable_item")
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'one'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk
            )
        )

    def test_edit_field(self):
        from django.contrib.admin import site

        exadmin = site._registry[Example1]
        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()

        request = self.get_page_request(page, user, edit_url)
        request.GET['edit_fields'] = 'char_1'
        response = exadmin.edit_field(request, ex1.pk, "en")
        self.assertContains(response, 'id="id_char_1"')
        self.assertContains(response, 'value="one"')

    def test_edit_field_not_allowed(self):
        from django.contrib.admin import site

        exadmin = site._registry[Example1]
        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex1 = self._get_example_obj()

        request = self.get_page_request(page, user, edit_url)
        request.GET['edit_fields'] = 'char_3'
        response = exadmin.edit_field(request, ex1.pk, "en")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Field char_3 not found')

    def test_edit_page(self):
        language = "en"
        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', language)
        title = page.get_content_obj(language)
        title.menu_title = 'Menu Test'
        title.page_title = 'Page Test'
        title.title = 'Main Test'
        title.save()
        page.reload()
        edit_url = get_object_edit_url(title)
        request = self.get_page_request(page, user, edit_url)
        response = details(request, page.get_path(language))
        response.render()
        self.assertContains(
            response,
            f'<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-get_page_title-{page.pk} cms-render-model">'
            '</template>'
            f'{page.get_page_title(language)}'
            f'<template class="cms-plugin cms-plugin-end cms-plugin-cms-page-get_page_title-{page.pk} cms-render-model">'
            '</template>'
        )
        self.assertContains(
            response,
            f'<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-get_menu_title-{page.pk} cms-render-model">'
            '</template>'
            f'{page.get_menu_title(language)}'
            f'<template class="cms-plugin cms-plugin-end cms-plugin-cms-page-get_menu_title-{page.pk} cms-render-model">'
            '</template>'
        )
        self.assertContains(
            response,
            f'<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-get_title-{page.pk} cms-render-model">'
            '</template>'
            f'{page.get_title(language)}'
            f'<template class="cms-plugin cms-plugin-end cms-plugin-cms-page-get_title-{page.pk} cms-render-model">'
            '</template>'
        )
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-changelist-%s cms-render-model '
            'cms-render-model-block"></template>\n        <h3>Menu</h3>' % page.pk
        )


class ToolbarUtilsTestCase(ToolbarTestBase):
    @override_settings(CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED=True)
    @override_settings(CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM="test-live-link")
    def test_add_live_url_querystring_param_no_querystring(self):
        """
        When the endpoint returns a value without a querystring param, one should be added to the
        url returned
        """
        page = create_page("home", 'nav_playground.html', "en")
        page_content = page.get_content_obj()
        live_url = page.get_absolute_url()

        edit_url = get_object_edit_url(page_content)
        preview_url = get_object_preview_url(page_content)

        self.assertIn(f"?test-live-link={live_url}", edit_url)
        self.assertIn(f"?test-live-link={live_url}", preview_url)
        self.assertEqual(edit_url.count("?"), 1)
        self.assertEqual(preview_url.count("?"), 1)
        self.assertEqual(edit_url.count("&"), 0)
        self.assertEqual(preview_url.count("&"), 0)

    @override_settings(CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED=True)
    @override_settings(CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM="test-live-link")
    @patch("cms.utils.urlutils.admin_reverse")
    def test_add_live_url_querystring_param_with_querystring(self, patched_admin_reverse):
        """
        With the endpoint returning an existing querystring param, the additional param should be appended
        to the existing with &.
        """
        page = create_page("home", 'nav_playground.html', "en")
        page_content = page.get_content_obj()
        app_label = page_content._meta.app_label
        model_name = page_content._meta.model_name
        live_url = page.get_absolute_url()
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        # Get the original edit endpoint url, and patch it with additional querystring parameter
        base_edit_url = admin_reverse('cms_placeholder_render_object_edit', args=[content_type.pk, page_content.pk])

        with patch.object(utils, "admin_reverse", return_value=f"{base_edit_url}?base_qsp=base_value"):
            edit_url = get_object_edit_url(page_content)

        # Get the original edit endpoint url, and patch it with additional querystring parameter
        base_preview_url = admin_reverse(
            'cms_placeholder_render_object_preview', args=[content_type.pk, page_content.pk]
        )

        with patch.object(utils, "admin_reverse", return_value=f"{base_preview_url}?base_qsp=base_value"):
            preview_url = get_object_edit_url(page_content)

        self.assertIn(f"?base_qsp=base_value&test-live-link={live_url}", edit_url)
        self.assertIn(f"?base_qsp=base_value&test-live-link={live_url}", preview_url)
        self.assertEqual(edit_url.count("?"), 1)
        self.assertEqual(preview_url.count("?"), 1)
        self.assertEqual(edit_url.count("&"), 1)
        self.assertEqual(preview_url.count("&"), 1)

    def test_add_live_url_querystring_param_no_querystring_setting_disabled(self):
        """
        With the querystring param configured, but CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED not set True,
        don't add the querystring params
        """
        page = create_page("home", 'nav_playground.html', "en")
        page_content = page.get_content_obj()
        content_type = ContentType.objects.get_for_model(page_content)
        language = get_language()
        with override(language):
            expected_edit_url = admin_reverse(
                'cms_placeholder_render_object_edit', args=[content_type.pk, page_content.pk]
            )
            expected_preview_url = admin_reverse(
                'cms_placeholder_render_object_preview', args=[content_type.pk, page_content.pk]
            )

        edit_url = get_object_edit_url(page_content)
        preview_url = get_object_preview_url(page_content)

        self.assertEqual(edit_url, expected_edit_url)
        self.assertEqual(preview_url, expected_preview_url)
        self.assertEqual(edit_url.count("?"), 0)
        self.assertEqual(preview_url.count("?"), 0)
        self.assertEqual(edit_url.count("&"), 0)
        self.assertEqual(preview_url.count("&"), 0)

    @override_settings(CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM="test-live-link")
    @override_settings(CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED=True)
    def test_add_live_url_querystring_param_handles_wrong_content_type(self):
        """
        With CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED set True, and
        CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM provided, but a content type that isn't PageContent provided,
        don't add the querystring params
        """
        test_obj = self._get_example_obj()
        content_type = ContentType.objects.get_for_model(test_obj)
        language = get_language()
        with override(language):
            expected_edit_url = admin_reverse(
                'cms_placeholder_render_object_edit', args=[content_type.pk, test_obj.pk]
            )
            expected_preview_url = admin_reverse(
                'cms_placeholder_render_object_preview', args=[content_type.pk, test_obj.pk]
            )
        edit_url = add_live_url_querystring_param(test_obj, expected_edit_url)
        preview_url = add_live_url_querystring_param(test_obj, expected_preview_url)

        self.assertEqual(edit_url, expected_edit_url)
        self.assertEqual(preview_url, expected_preview_url)
        self.assertEqual(edit_url.count("?"), 0)
        self.assertEqual(preview_url.count("?"), 0)

    def test_get_object_for_language_one_language(self):
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page, "en")

        self.assertEqual(page_content, get_object_for_language(page_content, "en"))
        self.assertTrue(not hasattr(page_content, "_sibling_objects_for_language_cache"))
        self.assertIsNone(get_object_for_language(page_content, "de"))
        self.assertTrue(hasattr(page_content, "_sibling_objects_for_language_cache"))
        self.assertEqual(len(page_content._sibling_objects_for_language_cache), 1)

    def test_get_object_for_language_multiple_languages(self):
        page = create_page('Test', 'col_two.html', 'en')
        # Additional pages to ensure not a page content of another page is returned
        for code, verbose in get_language_tuple():
            create_page(f"Not this page ({verbose})", "col_two.html", code)

        page_content = {
            "en": self.get_pagecontent_obj(page, "en")
        }
        for code, verbose in get_language_tuple():
            if code != "en":
                page_content[code] = create_page_content(code, verbose, page)

        self.assertEqual(page_content["en"], get_object_for_language(page_content["en"], "en"))
        self.assertTrue(not hasattr(page_content["en"], "_sibling_objects_for_language_cache"))
        self.assertEqual(get_object_for_language(page_content["en"], "de"), page_content["de"])
        self.assertTrue(hasattr(page_content["en"], "_sibling_objects_for_language_cache"))
        self.assertEqual(len(page_content["en"]._sibling_objects_for_language_cache), len(get_language_tuple()))


class CharPkFrontendPlaceholderAdminTest(ToolbarTestBase):

    def get_admin(self):
        admin.autodiscover()
        return admin.site._registry[CharPksExample]

    def test_url_char_pk(self):
        """
        Tests whether the frontend admin matches the edit_fields url with alphanumeric pks
        """
        ex = CharPksExample(
            char_1='one',
            slug='some-Special_slug_123',
        )
        ex.save()
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            response = self.client.get(admin_reverse('placeholderapp_charpksexample_edit_field', args=(ex.pk, 'en')),
                                       data={'edit_fields': 'char_1'})
            # if we get a response pattern matches
            self.assertEqual(response.status_code, 200)

    def test_url_numeric_pk(self):
        """
        Tests whether the frontend admin matches the edit_fields url with numeric pks
        """
        ex = self._get_example_obj()
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            response = self.client.get(admin_reverse('placeholderapp_example1_edit_field', args=(ex.pk, 'en')),
                                       data={'edit_fields': 'char_1'})
            # if we get a response pattern matches
            self.assertEqual(response.status_code, 200)

    def test_view_numeric_pk(self):
        """
        Tests whether the admin urls triggered when the toolbar is active works
        (i.e.: no NoReverseMatch is raised) with numeric pks
        """
        page = create_page('Test', 'col_two.html', 'en')
        page_content = self.get_pagecontent_obj(page)
        edit_url = get_object_edit_url(page_content)
        ex = self._get_example_obj()
        superuser = self.get_superuser()
        request = self.get_page_request(page, superuser, edit_url)
        response = detail_view(request, ex.pk)
        # if we get a response pattern matches
        self.assertEqual(response.status_code, 200)


class ToolbarAPITests(TestCase):
    def test_find_item(self):
        api = ToolbarAPIMixin()
        first = api.add_link_item('First', 'http://www.example.org')
        second = api.add_link_item('Second', 'http://www.example.org')
        all_links = api.find_items(LinkItem)
        self.assertEqual(len(all_links), 2)
        result = api.find_first(LinkItem, name='First')
        self.assertNotEqual(result, None)
        self.assertEqual(result.index, 0)
        self.assertEqual(result.item, first)
        result = api.find_first(LinkItem, name='Second')
        self.assertNotEqual(result, None)
        self.assertEqual(result.index, 1)
        self.assertEqual(result.item, second)
        no_result = api.find_first(LinkItem, name='Third')
        self.assertEqual(no_result, None)

    def test_find_item_lazy(self):
        lazy_attribute = lazy(lambda x: x, str)('Test')
        api = ToolbarAPIMixin()
        api.add_link_item(lazy_attribute, None)
        result = api.find_first(LinkItem, name='Test')
        self.assertNotEqual(result, None)
        self.assertEqual(result.index, 0)

    def test_not_is_staff(self):
        request = RequestFactory().get('/en/')
        request.session = {}
        request.LANGUAGE_CODE = 'en'
        request.user = AnonymousUser()
        toolbar = CMSToolbar(request)
        self.assertEqual(len(toolbar.get_left_items()), 0)
        self.assertEqual(len(toolbar.get_right_items()), 0)

    def test_item_search_result(self):
        item = object()
        result = ItemSearchResult(item, 2)
        self.assertEqual(result.item, item)
        self.assertEqual(int(result), 2)
        result += 2
        self.assertEqual(result.item, item)
        self.assertEqual(result.index, 4)


class TestLanguageMenu(CMSTestCase):
    @override_settings(
        LANGUAGE_CODE='en',
        LANGUAGES=(('en', 'English'),),
        CMS_LANGUAGES={
            1: [
                {'code': 'en',
                 'name': 'English',
                 'public': True},
            ],
        }
    )
    def test_no_language_menu(self):
        """No language menu appears if only one language is available"""
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        self.assertNotIn(LANGUAGE_MENU_IDENTIFIER, toolbar.menus)

    def test_language_menu(self):
        """A language menu appears if more than one language is available"""
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        self.assertIn(LANGUAGE_MENU_IDENTIFIER, toolbar.menus)
