from __future__ import with_statement
from cms.api import create_page, create_title
from cms.cms_toolbar import ADMIN_MENU_IDENTIFIER
from cms.toolbar.items import ToolbarAPIMixin, LinkItem, ItemSearchResult
from cms.toolbar.toolbar import CMSToolbar
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride

from django.contrib.auth.models import AnonymousUser, User, Permission
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.functional import lazy


class ToolbarTestBase(SettingsOverrideTestCase):
    def get_page_request(self, page, user, path=None, edit=False, lang_code='en'):
        path = path or page and page.get_absolute_url()
        if edit:
            path += '?edit'
        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.LANGUAGE_CODE = lang_code
        if edit:
            request.GET = {'edit': None}
        else:
            request.GET = {'edit_off': None}
        request.current_page = page
        mid = ToolbarMiddleware()
        mid.process_request(request)
        return request

    def get_anon(self):
        return AnonymousUser()

    def get_staff(self):
        staff = User(
            username='staff',
            email='staff@staff.org',
            is_active=True,
            is_staff=True,
        )
        staff.set_password('staff')
        staff.save()
        staff.user_permissions.add(Permission.objects.get(codename='change_page'))
        return staff

    def get_nonstaff(self):
        nonstaff = User(
            username='nonstaff',
            email='nonstaff@staff.org',
            is_active=True,
            is_staff=False,
        )
        nonstaff.set_password('nonstaff')
        nonstaff.save()
        nonstaff.user_permissions.add(Permission.objects.get(codename='change_page'))
        return nonstaff

    def get_superuser(self):
        superuser = User(
            username='superuser',
            email='superuser@superuser.org',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        superuser.set_password('superuser')
        superuser.save()
        return superuser


class ToolbarTests(ToolbarTestBase):
    settings_overrides = {'CMS_PERMISSION': False}

    def test_no_page_anon(self):
        request = self.get_page_request(None, self.get_anon(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 0)

    def test_no_page_staff(self):
        request = self.get_page_request(None, self.get_staff(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 3, items)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 6, admin_items)

    def test_no_page_superuser(self):
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 3)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 7, admin_items)

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

    def test_template_change_permission(self):
        with SettingsOverride(CMS_PERMISSIONS=True):
            page = create_page('test', 'nav_playground.html', 'en', published=True)
            request = self.get_page_request(page, self.get_nonstaff())
            toolbar = CMSToolbar(request)
            items = toolbar.get_left_items() + toolbar.get_right_items()
            self.assertEqual([item for item in items if item.css_class_suffix == 'templates'], [])

    def test_markup(self):
        create_page("toolbar-page", "nav_playground.html", "en", published=True)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get('/en/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'nav_playground.html')
        self.assertContains(response, '<div id="cms_toolbar"')
        self.assertContains(response, 'cms.placeholders.js')
        self.assertContains(response, 'cms.placeholders.css')

    def test_show_toolbar_to_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_with_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, AnonymousUser(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_without_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, AnonymousUser(), edit=False)
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_superuser(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 7)

    def test_no_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_staff(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

    def test_no_change_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        user = self.get_staff()
        user.user_permissions.all().delete()
        request = self.get_page_request(page, user, edit=True)
        toolbar = CMSToolbar(request)
        self.assertFalse(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))

        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + page-menu + admin-menu + logout
        self.assertEqual(len(items), 3, items)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 6, admin_items)

    def test_button_consistency_staff(self):
        """
        Tests that the buttons remain even when the language changes.
        """
        user = self.get_staff()
        cms_page = create_page('test-en', 'nav_playground.html', 'en', published=True)
        create_title('de', 'test-de', cms_page)
        en_request = self.get_page_request(cms_page, user, edit=True)
        en_toolbar = CMSToolbar(en_request)
        self.assertEqual(len(en_toolbar.get_left_items() + en_toolbar.get_right_items()), 6)
        de_request = self.get_page_request(cms_page, user, path='/de/', edit=True, lang_code='de')
        de_toolbar = CMSToolbar(de_request)
        self.assertEqual(len(de_toolbar.get_left_items() + de_toolbar.get_right_items()), 6)


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
        request = RequestFactory().get('/en/?edit')
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
