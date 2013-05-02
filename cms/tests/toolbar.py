from __future__ import with_statement
from cms.api import create_page
from cms.toolbar.toolbar import CMSToolbar
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride

from django.contrib.auth.models import AnonymousUser, User, Permission
from django.test.client import RequestFactory


class ToolbarTestBase(SettingsOverrideTestCase):
    def get_page_request(self, page, user, path=None, edit=False):
        path = page and page.get_absolute_url() or path
        if edit:
            path += '?edit'
        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
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

    def test_toolbar_no_page_anon(self):
        request = self.get_page_request(None, self.get_anon(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.items
        self.assertEqual(len(items), 0)

    def test_toolbar_no_page_staff(self):
        request = self.get_page_request(None, self.get_staff(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.items
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0].get_context()['items']), 4)

    def test_toolbar_no_page_superuser(self):
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.items
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0].get_context()['items']), 5)

    def test_toolbar_anon(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.get_page_request(page, self.get_anon())
        toolbar = CMSToolbar(request)

        items = toolbar.items
        self.assertEqual(len(items), 0)

    def test_toolbar_nonstaff(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_nonstaff())
        toolbar = CMSToolbar(request)
        items = toolbar.items
        # Logo + edit-mode + logout
        self.assertEqual(len(items), 0)

    def test_toolbar_template_change_permission(self):
        with SettingsOverride(CMS_PERMISSIONS=True):
            page = create_page('test', 'nav_playground.html', 'en', published=True)
            request = self.get_page_request(page, self.get_nonstaff())
            toolbar = CMSToolbar(request)
            items = toolbar.items
            self.assertEqual([item for item in items if item.css_class_suffix == 'templates'], [])

    def test_toolbar_markup(self):
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

    def test_toolbar_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_superuser(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.items
        self.assertEqual(len(items), 5)

    def test_toolbar_no_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_staff(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.items
        # Logo + edit-mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 4)

    def test_toolbar_no_change_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        user = self.get_staff()
        user.user_permissions.all().delete()
        request = self.get_page_request(page, user, edit=True)
        toolbar = CMSToolbar(request)
        self.assertFalse(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))

        items = toolbar.items
        # Logo + page-menu + admin-menu + logout
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0].get_context()['items']), 4)


