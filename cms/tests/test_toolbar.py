# -*- coding: utf-8 -*-

import datetime
import iptools
import re

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import truncatewords
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from cms.api import create_page, create_title, add_plugin
from cms.admin.forms import RequestToolbarForm
from cms.cms_toolbars import (ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK, get_user_model,
                              LANGUAGE_MENU_IDENTIFIER)
from cms.middleware.toolbar import ToolbarMiddleware
from cms.constants import PUBLISHER_STATE_DIRTY
from cms.models import Page, UserSettings, PagePermission
from cms.test_utils.project.placeholderapp.models import Example1, CharPksExample
from cms.test_utils.project.placeholderapp.views import detail_view, detail_view_char, ClassDetail
from cms.test_utils.testcases import (CMSTestCase,
                                      URL_CMS_PAGE_ADD, URL_CMS_PAGE_CHANGE,
                                      URL_CMS_USERSETTINGS)
from cms.test_utils.util.context_managers import UserLoginContext
from cms.toolbar_pool import toolbar_pool
from cms.toolbar.items import (ToolbarAPIMixin, LinkItem, ItemSearchResult,
                               Break, SubMenu, AjaxItem)
from cms.toolbar.toolbar import CMSToolbar
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_tuple
from cms.utils.urlutils import admin_reverse
from cms.views import details


class ToolbarTestBase(CMSTestCase):

    def get_page_request(self, page, user, path=None, edit=False,
                         preview=False, structure=False, lang_code='en', disable=False):
        if not path:
            path = page.get_absolute_url()

        if edit:
            path += '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')

        if structure:
            path += '?%s' % get_cms_setting('CMS_TOOLBAR_URL__BUILD')

        if preview:
            path += '?preview'

        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.LANGUAGE_CODE = lang_code
        if edit:
            request.GET = {'edit': None}
        else:
            request.GET = {'edit_off': None}
        if disable:
            request.GET[get_cms_setting('CMS_TOOLBAR_URL__DISABLE')] = None
        request.current_page = page
        mid = ToolbarMiddleware()
        mid.process_request(request)
        if hasattr(request,'toolbar'):
            request.toolbar.populate()
        return request

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

    def _fake_logentry(self, instance_id, user, text, model=Page):
        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(model).pk,
            object_id=instance_id,
            object_repr=text,
            action_flag=CHANGE,
        )
        entry = LogEntry.objects.filter(user=user, object_id=instance_id, action_flag__in=(CHANGE,))[0]
        session = self.client.session
        session['cms_log_latest'] = entry.pk
        session.save()


@override_settings(ROOT_URLCONF='cms.test_utils.project.nonroot_urls')
class ToolbarMiddlewareTest(ToolbarTestBase):
    @override_settings(CMS_TOOLBAR_HIDE=False)
    def test_no_app_setted_show_toolbar_in_non_cms_urls(self):
        request = self.get_page_request(None, self.get_anon(), '/en/example/')
        self.assertTrue(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=False)
    def test_no_app_setted_show_toolbar_in_cms_urls(self):
        page = create_page('foo', 'col_two.html', 'en', published=True)
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
        page = create_page('foo', 'col_two.html', 'en', published=True)
        page = create_page('foo', 'col_two.html', 'en', published=True, parent=page)
        request = self.get_page_request(page, self.get_anon())
        self.assertTrue(hasattr(request, 'toolbar'))

    @override_settings(CMS_TOOLBAR_HIDE=True)
    def test_app_setted_show_toolbar_in_cms_urls_subpage(self):
        page = create_page('foo', 'col_two.html', 'en', published=True)
        page = create_page('foo', 'col_two.html', 'en', published=True, parent=page)
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
        page_item = [item for item in items if force_text(item.name) == 'Page']
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

    def test_toolbar_login_non_staff(self):
        admin = self.get_nonstaff()
        endpoint = reverse('cms_login') + '?next=/en/admin/'
        username = getattr(admin, get_user_model().USERNAME_FIELD)
        password = getattr(admin, get_user_model().USERNAME_FIELD)
        response = self.client.post(endpoint, data={'username': username, 'password': password})
        self.assertRedirects(response, '/en/admin/?cms_toolbar_login_error=1', target_status_code=302)
        self.assertFalse(settings.SESSION_COOKIE_NAME in response.cookies)

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
        cms_page = create_page("toolbar-page", "col_two.html", "en", published=True)

        with self.login_user_context(self.get_superuser()):
            endpoint = cms_page.get_absolute_url() + '?' + get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
            response = self.client.get(endpoint)
            self.assertContains(response, '<script type="text/javascript" src="/static/samplemap/js/sampleapp.js"></script>')
            self.assertContains(response, '<link href="/static/samplemap/css/sampleapp.css"')
        toolbar_pool.toolbars = old_pool
        toolbar_pool._discovered = True

    def test_toolbar_request_endpoint_validation(self):
        endpoint = self.get_admin_url(UserSettings, 'get_toolbar')
        cms_page = create_page("toolbar-page", "col_two.html", "en", published=True)
        cms_page_2 = create_page("toolbar-page-2", "col_two.html", "en", published=True)

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(
                endpoint,
                data={
                    'obj_id': cms_page.pk,
                    'obj_type': 'cms.page',
                    'cms_path': cms_page.get_absolute_url('en')
                },
            )
            self.assertEqual(response.status_code, 200)

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

            # Page from path does not match attached toolbar obj
            response = self.client.get(
                endpoint,
                data={
                    'obj_id': cms_page.pk,
                    'obj_type': 'cms.page',
                    'cms_path': cms_page_2.get_absolute_url('en')
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_toolbar_request_form(self):
        cms_page = create_page("toolbar-page", "col_two.html", "en", published=True)
        generic_obj = Example1.objects.create(
            char_1="char_1",
            char_2="char_2",
            char_3="char_3",
            char_4="char_4",
        )

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
        # Logo + admin-menu + logout
        self.assertEqual(len(items), 3, items)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 12, admin_items)

    def test_no_page_superuser(self):
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 3)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 13, admin_items)

    def test_anon(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.get_page_request(page, self.get_anon())
        toolbar = CMSToolbar(request)

        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 0)

    def test_nonstaff(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_nonstaff())
        toolbar = CMSToolbar(request)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + logout
        self.assertEqual(len(items), 0)

    @override_settings(CMS_PERMISSION=True)
    def test_template_change_permission(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)

        # Staff user with change page permissions only
        staff_user = self.get_staff_user_with_no_permissions()
        self.add_permission(staff_user, 'change_page')
        global_permission = self.add_global_permission(staff_user, can_change=True, can_delete=True)

        # User should not see "Templates" option because he only has
        # "change" permission.
        request = self.get_page_request(page, staff_user, edit=True)
        toolbar = CMSToolbar(request)
        page_item = self.get_page_item(toolbar)
        template_item = [item for item in page_item.items
                         if force_text(getattr(item, 'name', '')) == 'Templates']
        self.assertEqual(len(template_item), 0)

        # Give the user change advanced settings permission
        global_permission.can_change_advanced_settings = True
        global_permission.save()

        # Reload user to avoid stale caches
        staff_user = self.reload(staff_user)

        # User should see "Templates" option because
        # he has "change advanced settings" permission
        request = self.get_page_request(page, staff_user, edit=True)
        toolbar = CMSToolbar(request)
        page_item = self.get_page_item(toolbar)
        template_item = [item for item in page_item.items
                         if force_text(getattr(item, 'name', '')) == 'Templates']
        self.assertEqual(len(template_item), 1)

    def test_markup(self):
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            response = self.client.get(page_edit_on_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'nav_playground.html')
        self.assertContains(response, '<div id="cms-top"')
        self.assertContains(response, 'cms.base.css')

    def test_live_draft_markup_on_app_page(self):
        """
        Checks that the "edit page" button shows up
        on non-cms pages with app placeholders and no static placeholders.
        """
        superuser = self.get_superuser()

        output = (
            '<a class="cms-btn cms-btn-action cms-btn-switch-edit" '
            'href="/en/example/latest/?{}">Edit</a>'
        ).format(get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))

        Example1.objects.create(
            char_1="char_1",
            char_2="char_2",
            char_3="char_3",
            char_4="char_4",
        )

        with self.login_user_context(superuser):
            response = self.client.get('/en/example/latest/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, output, html=True)

    def test_markup_generic_module(self):
        page = create_page("toolbar-page", "col_two.html", "en", published=True)
        page_structure_url = self.get_obj_structure_url(page.get_absolute_url())
        superuser = self.get_superuser()

        with self.login_user_context(superuser):
            response = self.client.get(page_structure_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="cms-submenu-item cms-submenu-item-title"><span>Generic</span>')

    def test_markup_link_custom_module(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "col_two.html", "en", published=True)
        page_structure_url = self.get_obj_structure_url(page.get_absolute_url())

        with self.login_user_context(superuser):
            response = self.client.get(page_structure_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="LinkPlugin">')
        self.assertContains(response,
                            '<div class="cms-submenu-item cms-submenu-item-title"><span>Different Grouper</span>')

    def test_extra_placeholder_menu_items(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "col_two.html", "en", published=True)
        page_structure_url = self.get_obj_structure_url(page.get_absolute_url())

        with self.login_user_context(superuser):
            response = self.client.get(page_structure_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<div class="cms-submenu-item"><a href="/some/url/" data-rel="ajax"'
        )
        self.assertContains(
            response,
            'data-on-success="REFRESH_PAGE" data-cms-icon="whatever" >Data item - not usable</a></div>'
        )
        self.assertContains(
            response,
            '<div class="cms-submenu-item"><a href="/some/other/url/" data-rel="ajax_add"'
        )

    def test_markup_toolbar_url_page(self):
        superuser = self.get_superuser()
        page_1 = create_page("top-page", "col_two.html", "en", published=True)
        page_2 = create_page("sec-page", "col_two.html", "en", published=True, parent=page_1)
        page_3 = create_page("trd-page", "col_two.html", "en", published=False, parent=page_1)

        # page with publish = draft
        # check when in draft mode
        with self.login_user_context(superuser):
            response = self.client.get('%s?%s' % (
                page_2.get_absolute_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s?preview&amp;%s"' % (
            page_2.get_public_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        ))
        # check when in live mode
        with self.login_user_context(superuser):
            response = self.client.get('%s?preview&%s' % (
                page_2.get_absolute_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s?%s"' % (
            page_2.get_draft_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        ))
        self.assertEqual(page_2.get_draft_url(), page_2.get_public_url())

        # page with publish != draft
        page_2.get_title_obj().slug = 'mod-page'
        page_2.get_title_obj().path = 'top-page/mod-page'
        page_2.get_title_obj().save()
        # check when in draft mode
        with self.login_user_context(superuser):
            response = self.client.get('%s?%s' % (
                page_2.get_absolute_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s?preview&amp;%s"' % (
            page_2.get_public_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        ))
        # check when in live mode
        with self.login_user_context(superuser):
            response = self.client.get('%s?preview&%s' % (
                page_2.get_public_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s?%s"' % (
            page_2.get_draft_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        ))
        self.assertNotEqual(page_2.get_draft_url(), page_2.get_public_url())

        # not published page
        # check when in draft mode
        with self.login_user_context(superuser):
            response = self.client.get('%s?%s' % (
                page_3.get_absolute_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'cms-toolbar-item-switch')
        self.assertEqual(page_3.get_public_url(), '')
        self.assertNotEqual(page_3.get_draft_url(), page_3.get_public_url())

    def test_markup_plugin_template(self):
        page = create_page("toolbar-page-1", "col_two.html", "en", published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())
        plugin_1 = add_plugin(page.placeholders.get(slot='col_left'), language='en',
                              plugin_type='TestPluginAlpha', alpha='alpha')
        plugin_2 = add_plugin(page.placeholders.get(slot='col_left'), language='en',
                              plugin_type='TextPlugin', body='text')
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_on_url)
        self.assertEqual(response.status_code, 200)
        response_text = response.render().rendered_content
        self.assertTrue(re.search('edit_plugin.+/admin/custom/view/%s' % plugin_1.pk, response_text))
        self.assertTrue(re.search('move_plugin.+/admin/custom/move/', response_text))
        self.assertTrue(re.search('delete_plugin.+/admin/custom/delete/%s/' % plugin_1.pk, response_text))
        self.assertTrue(re.search('add_plugin.+/admin/custom/view/', response_text))
        self.assertTrue(re.search('copy_plugin.+/admin/custom/copy/', response_text))

        self.assertTrue(re.search('edit_plugin.+/en/admin/cms/page/edit-plugin/%s' % plugin_2.pk, response_text))
        self.assertTrue(re.search('delete_plugin.+/en/admin/cms/page/delete-plugin/%s/' % plugin_2.pk, response_text))

    def test_show_toolbar_to_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        staff = self.get_staff()
        assert staff.user_permissions.get().name == 'Can change page'
        request = self.get_page_request(page, staff, '/')
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_with_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, AnonymousUser(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_staff(), edit=True)
        self.assertTrue(request.session.get('cms_edit', False))

    def test_hide_toolbar_non_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_nonstaff(), edit=True)
        self.assertNotIn('cms_edit', request.session)

    def test_hide_toolbar_disabled(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        # Edit mode should re-enable the toolbar in any case
        request = self.get_page_request(page, self.get_staff(), edit=False, disable=True)
        self.assertTrue(request.session.get('cms_toolbar_disabled'))
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_show_disabled_toolbar_with_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_staff(), edit=True, disable=True)
        self.assertFalse(request.session.get('cms_toolbar_disabled'))
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_toolbar_login_redirect_validation(self):
        user = self._create_user('toolbar', True, True)
        username = getattr(user, user.USERNAME_FIELD)
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        page.set_as_homepage()
        login_url = reverse('cms_login')
        endpoint = '{}?next=https://notyourdomain.com'.format(login_url)
        response = self.client.post(endpoint, {'username': username, 'password': username})
        self.assertRedirects(response, page.get_absolute_url(), fetch_redirect_response=False)

    def test_show_toolbar_login_anonymous(self):
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())
        response = self.client.get(page_edit_on_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cms-form-login')

    @override_settings(CMS_TOOLBAR_ANONYMOUS_ON=False)
    def test_hide_toolbar_login_anonymous_setting(self):
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())
        response = self.client.get(page_edit_on_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'cms-form-login')

    def test_hide_toolbar_login_nonstaff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())

        with self.login_user_context(self.get_nonstaff()):
            response = self.client.get(page_edit_on_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'cms-form-login')
        self.assertNotContains(response, 'cms-toolbar')

    def test_admin_logout_staff(self):
        with override_settings(CMS_PERMISSION=True):
            with self.login_user_context(self.get_staff()):
                response = self.client.get('/en/admin/logout/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
                self.assertTrue(response.status_code, 200)

    def test_show_toolbar_without_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, AnonymousUser(), edit=False)
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        # Needed because publish button only shows if the page is dirty
        page.set_publisher_state('en', state=PUBLISHER_STATE_DIRTY)

        request = self.get_page_request(page, self.get_superuser(), edit=True)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertTrue(toolbar.edit_mode_active)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 7)

    def test_no_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        user = self.get_staff()
        request = self.get_page_request(page, user, edit=True)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertTrue(page.has_change_permission(request.user))
        self.assertFalse(page.has_publish_permission(request.user))
        self.assertTrue(toolbar.edit_mode_active)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 5)

        # adding back structure mode permission
        permission = Permission.objects.get(codename='use_structure')
        user.user_permissions.add(permission)

        request.user = get_user_model().objects.get(pk=user.pk)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

    def test_no_change_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        user = self.get_staff()
        user.user_permissions.all().delete()
        request = self.get_page_request(page, user, edit=True)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertFalse(page.has_change_permission(request.user))
        self.assertFalse(page.has_publish_permission(request.user))

        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + page-menu + admin-menu + logout
        self.assertEqual(len(items), 4, items)
        page_items = items[1].get_items()
        # The page menu should only have the "Create page" item enabled.
        self.assertFalse(page_items[0].disabled)
        self.assertTrue(all(item.disabled for item in page_items[1:] if hasattr(item, 'disabled')))
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 14, admin_items)

    def test_button_consistency_staff(self):
        """
        Tests that the buttons remain even when the language changes.
        """
        user = self.get_staff()
        cms_page = create_page('test-en', 'nav_playground.html', 'en', published=True)
        create_title('de', 'test-de', cms_page)
        cms_page.publish('de')
        en_request = self.get_page_request(cms_page, user, edit=True)
        en_toolbar = CMSToolbar(en_request)
        en_toolbar.populate()
        en_toolbar.post_template_populate()
        # Logo + templates + page-menu + admin-menu + logout
        self.assertEqual(len(en_toolbar.get_left_items() + en_toolbar.get_right_items()), 5)
        de_request = self.get_page_request(cms_page, user, path='/de/', edit=True, lang_code='de')
        de_toolbar = CMSToolbar(de_request)
        de_toolbar.populate()
        de_toolbar.post_template_populate()
        # Logo + templates + page-menu + admin-menu + logout
        self.assertEqual(len(de_toolbar.get_left_items() + de_toolbar.get_right_items()), 5)

    def test_double_menus(self):
        """
        Tests that even called multiple times, admin and language buttons are not duplicated
        """
        user = self.get_staff()
        en_request = self.get_page_request(None, user, edit=True, path='/')
        toolbar = CMSToolbar(en_request)
        toolbar.populated = False
        toolbar.populate()
        toolbar.populated = False
        toolbar.populate()
        toolbar.populated = False
        toolbar.post_template_populate()
        admin = toolbar.get_left_items()[0]
        lang = toolbar.get_left_items()[1]
        self.assertEqual(len(admin.get_items()), 15)
        self.assertEqual(len(lang.get_items()), len(get_language_tuple(1)))

    @override_settings(CMS_PLACEHOLDER_CONF={'col_left': {'name': 'PPPP'}})
    def test_placeholder_name(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "col_two.html", "en", published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())

        with self.login_user_context(superuser):
            response = self.client.get(page_edit_on_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PPPP')

    def test_user_settings(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(URL_CMS_USERSETTINGS)
            self.assertEqual(response.status_code, 200)

    def test_remove_lang(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        page_edit_on_url = self.get_edit_on_url(page.get_absolute_url())
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(page_edit_on_url)
            self.assertEqual(response.status_code, 200)
            setting = UserSettings.objects.get(user=superuser)
            setting.language = 'it'
            setting.save()
            with self.settings(LANGUAGES=(('en', 'english'),)):
                response = self.client.get(page_edit_on_url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, '/it/')

    def test_get_alphabetical_insert_position(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
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
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        menu1 = toolbar.get_or_create_menu("test")
        menu2 = toolbar.get_or_create_menu("test", "Test", side=toolbar.RIGHT, position=2)

        self.assertEqual(menu1, menu2)
        self.assertEqual(menu1.name, 'Test')
        self.assertEqual(len(toolbar.get_right_items()), 1)

    def test_negative_position_left(self):
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        # Starting point: [Menu:Example, Menu:Page, Menu:Language]
        # Example @ 1, Page @ 2, Language @ -1
        menu1 = toolbar.get_or_create_menu("menu1", "Menu1", side=toolbar.LEFT, position=-2)
        menu2 = toolbar.get_or_create_menu("menu2", "Menu2", side=toolbar.LEFT, position=-3)
        self.assertEqual(toolbar.get_left_items().index(menu1), 3)
        self.assertEqual(toolbar.get_left_items().index(menu2), 2)

    def test_negative_position_right(self):
        page = create_page("toolbar-page", "nav_playground.html", "en", published=True)
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        # Starting point: [] (empty)
        # Add a couple of "normal" menus
        toolbar.get_or_create_menu("menu1", "Menu1", side=toolbar.RIGHT)
        toolbar.get_or_create_menu("menu2", "Menu2", side=toolbar.RIGHT)
        menu3 = toolbar.get_or_create_menu("menu3", "Menu3", side=toolbar.RIGHT, position=-1)
        menu4 = toolbar.get_or_create_menu("menu4", "Menu4", side=toolbar.RIGHT, position=-2)
        self.assertEqual(toolbar.get_right_items().index(menu3), 3)
        self.assertEqual(toolbar.get_right_items().index(menu4), 2)

    def test_page_create_redirect(self):
        superuser = self.get_superuser()
        page = self.create_homepage("home", "nav_playground.html", "en", published=True)
        resolve_url_on = '%s?%s' % (admin_reverse('cms_page_resolve'),
                                    get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        resolve_url_off = '%s?%s' % (admin_reverse('cms_page_resolve'),
                                     get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
        with self.login_user_context(superuser):
            response = self.client.post(resolve_url_on, {'pk': '', 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '')
            page_data = self.get_new_page_data(parent_id=page.node.pk)
            response = self.client.post(self.get_admin_url(Page, 'add'), page_data)
            self.assertRedirects(response, self.get_admin_url(Page, 'changelist'))

            public_home = Page.objects.public().get(is_home=True)

            # test redirection when toolbar is in edit mode
            response = self.client.post(resolve_url_on, {'pk': public_home.pk,
                                                         'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '/en/test-page-1/')

            self.client.post(URL_CMS_PAGE_ADD, page_data)

            # test redirection when toolbar is not in edit mode
            response = self.client.post(resolve_url_off, {'pk': public_home.pk,
                                                          'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '/en/')

    def test_page_edit_redirect_editmode(self):
        page1 = self.create_homepage("home", "nav_playground.html", "en", published=True)
        page2 = create_page("test", "nav_playground.html", "en",
                            published=True)
        page3 = create_page("non-pub", "nav_playground.html", "en",
                            published=False)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            page_data = self.get_new_page_data()
            self.client.post(URL_CMS_PAGE_CHANGE % page2.pk, page_data)
            url = '%s?%s' % (admin_reverse('cms_page_resolve'),
                             get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            # first call returns the latest modified page with updated slug even if a different
            # page has been requested
            response = self.client.post(url, {'pk': page1.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '/en/test-page-1/')
            # following call returns the actual page requested
            response = self.client.post(url, {'pk': page1.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '/en/')
            # non published page - staff user can access it
            response = self.client.post(url, {'pk': page3.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '/en/non-pub/')
        # anonymous users should be redirected to the root page
        response = self.client.post(url, {'pk': page3.pk, 'model': 'cms.page'})
        self.assertEqual(response.content.decode('utf-8'), '/')

    def test_page_edit_redirect_no_editmode(self):
        page1 = create_page("home", "nav_playground.html", "en",
                            published=True)
        page2 = create_page("test", "nav_playground.html", "en",
                            published=True, parent=page1)
        page3 = create_page("non-pub-1", "nav_playground.html", "en",
                            published=False, parent=page2)
        page4 = create_page("non-pub-2", "nav_playground.html", "en",
                            published=False, parent=page3)
        superuser = self.get_superuser()
        url = admin_reverse('cms_page_resolve')
        with self.login_user_context(superuser):
            # checking the redirect by passing URL parameters
            # redirect to the same page
            response = self.client.post(url, {'pk': page1.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), page1.get_absolute_url())
            # redirect to the same page
            response = self.client.post(url, {'pk': page2.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), page2.get_absolute_url())
            # redirect to the first published ancestor
            response = self.client.post(url, {'pk': page3.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '%s?%s' % (
                page3.get_absolute_url(),
                get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            )
            # redirect to the first published ancestor
            response = self.client.post(url, {'pk': page4.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '%s?%s' % (
                page4.get_absolute_url(),
                get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            )

            # checking the redirect by setting the session data
            self._fake_logentry(page1.get_draft_object().pk, superuser, 'test page')
            response = self.client.post(url, {'pk': page2.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), page1.get_public_object().get_absolute_url())

            self._fake_logentry(page2.get_draft_object().pk, superuser, 'test page')
            response = self.client.post(url, {'pk': page1.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), page2.get_public_object().get_absolute_url())

            self._fake_logentry(page3.get_draft_object().pk, superuser, 'test page')
            response = self.client.post(url, {'pk': page1.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '%s?%s' % (
                page3.get_absolute_url(),
                get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            )

            self._fake_logentry(page4.get_draft_object().pk, superuser, 'test page')
            response = self.client.post(url, {'pk': page1.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '%s?%s' % (
                page4.get_absolute_url(),
                get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            )

    def test_page_edit_redirect_errors(self):
        page1 = create_page("home", "nav_playground.html", "en",
                            published=True)
        page2 = create_page("test", "nav_playground.html", "en",
                            published=True, parent=page1)
        create_page("non-pub", "nav_playground.html", "en",
                    published=False, parent=page2)
        superuser = self.get_superuser()
        url = admin_reverse('cms_page_resolve')

        with self.login_user_context(superuser):
            # logentry - non existing id - parameter is used
            self._fake_logentry(9999, superuser, 'test page')
            response = self.client.post(url, {'pk': page2.pk, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), page2.get_public_object().get_absolute_url())
            # parameters - non existing id - no redirection
            response = self.client.post(url, {'pk': 9999, 'model': 'cms.page'})
            self.assertEqual(response.content.decode('utf-8'), '')

    def assertMenuItems(self, request, menu_id, name, items=None):
        toolbar = CMSToolbar(request)
        toolbar.populate()
        menu = dict(
            (force_text(getattr(item, 'name', '|')), item)
            for item in toolbar.get_menu(menu_id).get_items()
        )
        self.assertIn(name, list(menu))
        if items is not None:
            sub_menu = list(
                force_text(getattr(item, 'name', '|')) for item in menu[name].get_items()
            )
            self.assertEqual(sorted(sub_menu), sorted(items))

    def test_remove_language(self):
        page = create_page(
            "toolbar-page", "nav_playground.html", "en", published=True
        )
        create_title(title="de page", language="de", page=page)
        create_title(title="fr page", language="fr", page=page)

        request = self.get_page_request(page, self.get_staff(), '/', edit=True)

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
        page = create_page("tbp", "nav_playground.html", "en", published=True)
        request = self.get_page_request(page, self.get_staff(), '/', edit=True)
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Add Translation',
            [u'German...', u'Brazilian Portuguese...', u'French...', u'Espa\xf1ol...']
        )

        create_title(title="de page", language="de", page=page)
        create_title(title="fr page", language="fr", page=page)
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Add Translation',
            [u'Brazilian Portuguese...', u'Espa\xf1ol...']
        )

    def test_copy_plugins(self):
        page = create_page("tbp", "nav_playground.html", "en", published=True)
        create_title('de', 'de page', page)
        add_plugin(page.placeholders.get(slot='body'), "TextPlugin", "de", body='de body')
        create_title('fr', 'fr page', page)
        add_plugin(page.placeholders.get(slot='body'), "TextPlugin", "fr", body='fr body')
        page.publish('de')
        page.publish('fr')

        staff = self.get_staff()

        request = self.get_page_request(page, staff, '/', edit=True)
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Copy all plugins',
            [u'from German', u'from French']
        )

        request = self.get_page_request(page, staff, '/', edit=True, lang_code='de')
        self.assertMenuItems(
            request, LANGUAGE_MENU_IDENTIFIER, 'Copy all plugins',
            [u'from English', u'from French']
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

        page = create_page("home", "nav_playground.html", "en",
                           published=True)
        page.publish('en')
        self.get_page_request(page, superuser, '/')
        #
        # Test that the logout shows the username of the logged-in user if
        # first_name and last_name haven't been provided.
        #
        with self.login_user_context(superuser):
            response = self.client.get(page.get_absolute_url('en') + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertTrue(admin_menu.find_first(AjaxItem, name=_(u'Logout %s') % self.get_username(superuser)))

        #
        # Test that the logout shows the logged-in user's name, if it was
        # populated in auth.User.
        #
        superuser.first_name = 'Super'
        superuser.last_name = 'User'
        superuser.save()
        # Sanity check...
        self.get_page_request(page, superuser, '/')
        with self.login_user_context(superuser):
            response = self.client.get(page.get_absolute_url('en') + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertTrue(admin_menu.find_first(AjaxItem, name=_(u'Logout %s') % self.get_username(superuser)))

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
        page0 = create_page("home", "nav_playground.html", "en",
                            published=True)
        page1 = create_page("internal", "nav_playground.html", "en",
                            published=True, parent=page0)
        page2 = create_page("unpublished", "nav_playground.html", "en",
                            published=False, parent=page0)
        page3 = create_page("login_restricted", "nav_playground.html", "en",
                            published=True, parent=page0, login_required=True)
        page4 = create_page("view_restricted", "nav_playground.html", "en",
                            published=True, parent=page0)
        PagePermission.objects.create(page=page4, can_view=True,
                                      user=superuser)
        page4.publish('en')
        page4 = page4.get_public_object()
        self.get_page_request(page4, superuser, '/')

        with self.login_user_context(superuser):
            # Published page, no redirect
            response = self.client.get(page1.get_absolute_url('en') + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            toolbar = response.context['request'].toolbar
            menu_name = _(u'Logout %s') % self.get_username(superuser)
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertTrue(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success)

            # Unpublished page, redirect
            response = self.client.get(page2.get_absolute_url('en') + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)

            self.assertEquals(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success, '/')

            # Published page with login restrictions, redirect
            response = self.client.get(page3.get_absolute_url('en') + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertEquals(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success, '/')

            # Published page with view permissions, redirect
            response = self.client.get(page4.get_absolute_url('en') + '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
            toolbar = response.context['request'].toolbar
            admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            self.assertEquals(admin_menu.find_first(AjaxItem, name=menu_name).item.on_success, '/')


@override_settings(ROOT_URLCONF='cms.test_utils.project.placeholderapp_urls')
class EditModelTemplateTagTest(ToolbarTestBase):
    edit_fields_rx = "(\?|&amp;)edit_fields=%s"

    def tearDown(self):
        Example1.objects.all().delete()
        super(EditModelTemplateTagTest, self).tearDown()

    def test_markup_toolbar_url_model(self):
        superuser = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        # object
        # check when in draft mode
        request = self.get_page_request(page, superuser, edit=True)
        response = detail_view(request, ex1.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s?preview&amp;%s"' % (
            ex1.get_public_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        ))
        # check when in live mode
        request = self.get_page_request(page, superuser, preview=True)
        response = detail_view(request, ex1.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s?%s"' % (
            ex1.get_draft_url(), get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        ))
        self.assertNotEqual(ex1.get_draft_url(), ex1.get_public_url())

    def test_anon(self):
        user = self.get_anon()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, "<h1>char_1</h1>")
        self.assertNotContains(response, "CMS.API")

    def test_noedit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, "<h1>char_1</h1>")
        self.assertContains(response, "CMS.API")

    def test_edit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk)
        self.assertContains(
            response,
            '<h1><template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template></h1>'.format(
                'placeholderapp', 'example1', 'char_1', ex1.pk))

    def test_invalid_item(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model fake "char_1" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-%s cms-render-model"></template>' % ex1.pk)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-end cms-plugin-%s cms-render-model"></template>' % ex1.pk)

    def test_as_varname(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" as tempvar %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
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
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        render_placeholder_body = "I'm the render placeholder body"

        plugin = add_plugin(ex1.placeholder, u"TextPlugin", u"en", body=render_placeholder_body)

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_placeholder instance.placeholder %}</h1>
<h2>{% render_placeholder instance.placeholder as tempvar %}</h2>
<h3>{{ tempvar }}</h3>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<div class="cms-placeholder cms-placeholder-{0}"></div>'.format(ex1.placeholder.pk))

        self.assertContains(
            response,
            '<h1><template class="cms-plugin cms-plugin-start cms-plugin-{0}"></template>'
            '{1}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}"></template>'.format(
                                                                           plugin.pk, render_placeholder_body))

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
            '<h3>{0}</h3>'.format(render_placeholder_body)
            )

        self.assertContains(
            response,
            'CMS._plugins.push(["cms-plugin-{0}"'.format(plugin.pk)
        )

        self.assertContains(
            response,
            'CMS._plugins.push(["cms-placeholder-{0}"'.format(ex1.placeholder.pk)
        )

    def test_filters(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
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
        request = self.get_page_request(page, user, edit=True)
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
        request = self.get_page_request(page, user, edit=True)
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
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4")
        ex1.save()

        request = self.get_page_request(page, user, edit=True)
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
            page = create_page('Test', 'col_two.html', 'en', published=True)
            ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                           char_3="char_3",
                           char_4="char_4", date_field=datetime.date(2012, 1, 2))
            ex1.save()
            template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" %}</h1>
{% endblock content %}
'''

            request = self.get_page_request(page, user, edit=True)
            response = detail_view(request, ex1.pk, template_string=template_text)
            self.assertContains(
                response,
                '<h1>'
                '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '{4}'
                '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
                '</h1>'.format(
                    'placeholderapp', 'example1', 'date_field', ex1.pk,
                    ex1.date_field.strftime("%b. %d, %Y")))

            template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" "" "" "safe" %}</h1>
{% endblock content %}
'''
            request = self.get_page_request(page, user, edit=True)
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
        page = create_page('Test', 'col_two.html', 'en', published=True)
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

        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<h1>%s</h1>' % truncatewords(escape(ex1.char_1), 2))

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2|safe' "" "" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<h1>%s</h1>' % truncatewords(ex1.char_1, 2))

    def test_no_cms(self):
        user = self.get_staff()
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance %}
{% endblock content %}
'''
        request = self.get_page_request(None, user, path='/', edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'.format(
                'placeholderapp', 'example1', ex1.pk))
        self.assertContains(response, "onClose: 'REFRESH_PAGE',")

    def test_icon_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'.format(
                'placeholderapp', 'example1', ex1.pk))

    def test_icon_followed_by_render_model_block_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4", date_field=datetime.date(2012, 1, 1))
        ex1.save()
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
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            "CMS._plugins.push(['cms-plugin-{0}-{1}-{2}-{3}'".format('placeholderapp', 'example1', 'char_1', ex1.pk))

        self.assertContains(
            response,
            "CMS._plugins.push(['cms-plugin-{0}-{1}-{2}-{3}'".format('placeholderapp', 'example1', 'char_2', ex1.pk))

    def test_add_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'.format(
                'placeholderapp', 'example1', ex1.pk)
            )

    def test_add_tag_class(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance_class %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'.format(
                'placeholderapp', 'example1', '0'))

    def test_add_tag_classview(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance_class %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        view_func = ClassDetail.as_view(template_string=template_text)
        response = view_func(request, pk=ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'
            '<img src="/static/cms/img/toolbar/render_model_placeholder.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-add-{2} cms-render-model-add"></template>'.format(
                'placeholderapp', 'example1', '0'))

    def test_block_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
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
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertNotContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'
            '<img src="/static/cms/img/toolbar/render_model_icon.png">'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2} cms-render-model-icon"></template>'.format(
                'placeholderapp', 'example1', ex1.pk))

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
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model cms-render-model-block">'.format(
                'placeholderapp', 'example1', ex1.pk))
        self.assertContains(response, '<h1>%s - %s</h1>' % (ex1.char_1, ex1.char_2))
        self.assertContains(response, '<span class="date">%s</span>' % (ex1.date_field.strftime("%Y")))
        self.assertContains(response, '<a href="%s">successful if</a>\n    \n<template' % (reverse('detail', args=(ex1.pk,))))

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
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2} cms-render-model cms-render-model-block">'.format(
                'placeholderapp', 'example1', ex1.pk))
        self.assertContains(response, '<h1>%s - %s</h1>' % (ex1.char_1, ex1.char_2))
        self.assertContains(response, '<span class="date">%s</span>' % (ex1.date_field.strftime("%Y")))
        self.assertContains(response, '<a href="%s">successful if</a>\n    \n<template' % (reverse('detail', args=(ex1.pk,))))

        # Changelist check
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_block instance 'changelist' %}
    {{ instance }}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-changelist-{2} cms-render-model cms-render-model-block"></template>'.format(
                'placeholderapp', 'example1', ex1.pk))
        self.assertContains(
            response,
            "edit_plugin: '%s?language=%s&amp;edit_fields=changelist'" % (admin_reverse('placeholderapp_example1_changelist'), 'en'))

    def test_invalid_attribute(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "fake_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'.format(
                'placeholderapp', 'example1', 'fake_field', ex1.pk))
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'.format(
                'placeholderapp', 'example1', 'fake_field', ex1.pk))

        # no attribute
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0} cms-render-model"></template>'.format(ex1.pk))
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0} cms-render-model"></template>'.format(ex1.pk))

    def test_callable_item(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1><template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template></h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_view_method(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "" "dynamic_url" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response, "edit_plugin: '/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)

    def test_view_url(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response, "edit_plugin: '/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)

    def test_method_attribute(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "" "static_admin_url" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        ex1.set_static_url(request)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_admin_url(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        expected_output = (
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'
        ).format('placeholderapp', 'example1', 'callable_item', ex1.pk)
        self.assertContains(response, expected_output)

    def test_admin_url_extra_field(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_2" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk))
        self.assertContains(response, "/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_2", response.content.decode('utf8')))

    def test_admin_url_multiple_fields(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk))
        self.assertContains(response, "/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_1", response.content.decode('utf8')))
        self.assertTrue(re.search(self.edit_fields_rx % "char_1%2Cchar_2", response.content.decode('utf8')))

    def test_instance_method(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_item_from_context(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance item_name %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text,
                               item_name="callable_item")
        self.assertContains(
            response,
            '<h1>'
            '<template class="cms-plugin cms-plugin-start cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            'char_1'
            '<template class="cms-plugin cms-plugin-end cms-plugin-{0}-{1}-{2}-{3} cms-render-model"></template>'
            '</h1>'.format(
                'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_edit_field(self):
        from django.contrib.admin import site

        exadmin = site._registry[Example1]

        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        request = self.get_page_request(page, user, edit=True)
        request.GET['edit_fields'] = 'char_1'
        response = exadmin.edit_field(request, ex1.pk, "en")
        self.assertContains(response, 'id="id_char_1"')
        self.assertContains(response, 'value="char_1"')

    def test_edit_field_not_allowed(self):
        from django.contrib.admin import site

        exadmin = site._registry[Example1]

        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        request = self.get_page_request(page, user, edit=True)
        request.GET['edit_fields'] = 'char_3'
        response = exadmin.edit_field(request, ex1.pk, "en")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Field char_3 not found')

    def test_edit_page(self):
        language = "en"
        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', language, published=True)
        title = page.get_title_obj(language)
        title.menu_title = 'Menu Test'
        title.page_title = 'Page Test'
        title.title = 'Main Test'
        title.save()
        page.publish('en')
        page.reload()
        request = self.get_page_request(page, user, edit=True)
        response = details(request, page.get_path())
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-get_page_title-{0} cms-render-model"></template>'
            '{1}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-cms-page-get_page_title-{0} cms-render-model"></template>'.format(
                page.pk, page.get_page_title(language)))
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-get_menu_title-{0} cms-render-model"></template>'
            '{1}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-cms-page-get_menu_title-{0} cms-render-model"></template>'.format(
                page.pk, page.get_menu_title(language)))
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-get_title-{0} cms-render-model"></template>'
            '{1}'
            '<template class="cms-plugin cms-plugin-end cms-plugin-cms-page-get_title-{0} cms-render-model"></template>'.format(
                page.pk, page.get_title(language)))
        self.assertContains(
            response,
            '<template class="cms-plugin cms-plugin-start cms-plugin-cms-page-changelist-%s cms-render-model cms-render-model-block"></template>\n        <h3>Menu</h3>' % page.pk)
        self.assertContains(
            response,
            "edit_plugin: '%s?language=%s&amp;edit_fields=changelist'" % (admin_reverse('cms_page_changelist'), language))

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
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        superuser = self.get_superuser()
        with UserLoginContext(self, superuser):
            response = self.client.get(admin_reverse('placeholderapp_example1_edit_field', args=(ex.pk, 'en')),
                                       data={'edit_fields': 'char_1'})
            # if we get a response pattern matches
            self.assertEqual(response.status_code, 200)

    def test_view_char_pk(self):
        """
        Tests whether the admin urls triggered when the toolbar is active works
        (i.e.: no NoReverseMatch is raised) with alphanumeric pks
        """
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex = CharPksExample(
            char_1='one',
            slug='some-Special_slug_123',
        )
        ex.save()
        superuser = self.get_superuser()
        request = self.get_page_request(page, superuser, edit=True)
        response = detail_view_char(request, ex.pk)
        # if we get a response pattern matches
        self.assertEqual(response.status_code, 200)

    def test_view_numeric_pk(self):
        """
        Tests whether the admin urls triggered when the toolbar is active works
        (i.e.: no NoReverseMatch is raised) with numeric pks
        """
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex = Example1(
            char_1='one',
            char_2='two',
            char_3='tree',
            char_4='four'
        )
        ex.save()
        superuser = self.get_superuser()
        request = self.get_page_request(page, superuser, edit=True)
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
        request = RequestFactory().get('/en/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
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
