from __future__ import with_statement
from cms.api import create_page
from cms.cms_toolbar import CMSToolbar
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.toolbar.items import (Anchor, TemplateHTML, Switcher, List, ListItem, 
    GetButton)
from cms.utils import get_cms_setting
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

class ToolbarTestBase(SettingsOverrideTestCase):

    def get_page_request(self, page, user, path=None, edit=False):
        path = page and page.get_absolute_url() or path
        if edit:
            path += '?edit'
        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.current_page = page
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

        items = toolbar.get_items({})
        self.assertEqual(len(items), 2) # Logo + login

        # check the logo is there
        logo = items[0]
        self.assertIsInstance(logo, Anchor)

        # check the login form is there
        login = items[1]
        self.assertIsInstance(login, TemplateHTML)
        self.assertEqual(login.template, 'cms/toolbar/items/login.html')

    def test_toolbar_no_page_staff(self):
        request = self.get_page_request(None, self.get_staff(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 4)

        # check the logo is there
        logo = items[0]
        self.assertIsInstance(logo, Anchor)

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertIsInstance(edit, Switcher)
        self.assertFalse(toolbar.edit_mode)

        # check the admin-menu
        admin = items[2]
        self.assertIsInstance(admin, List)
        self.assertEqual(len(admin.raw_items), 1) # only the link to main admin
        self.assertIsInstance(admin.raw_items[0], ListItem)

        # check the logout button
        logout = items[-1]
        self.assertIsInstance(logout, GetButton)
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_no_page_superuser(self):
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 4)
        # check the logo is there
        logo = items[0]
        self.assertIsInstance(logo, Anchor)

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertIsInstance(edit, Switcher)
        self.assertFalse(toolbar.edit_mode)

        # check the admin-menu
        admin = items[2]
        self.assertIsInstance(admin, List)
        self.assertEqual(len(admin.raw_items), 1) # only the link to main admin
        self.assertIsInstance(admin.raw_items[0], ListItem)

        # check the logout button
        logout = items[-1]
        self.assertIsInstance(logout, GetButton)
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_anon(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.get_page_request(page, self.get_anon())
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        self.assertEqual(len(items), 2) # Logo + login

        # check the logo is there
        logo = items[0]
        self.assertIsInstance(logo, Anchor)

        # check the login form is there
        login = items[1]
        self.assertIsInstance(login, TemplateHTML)
        self.assertEqual(login.template, 'cms/toolbar/items/login.html')

    def test_toolbar_nonstaff(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_nonstaff())
        toolbar = CMSToolbar(request)
        items = toolbar.get_items({})
        # Logo + edit-mode + logout
        self.assertEqual(len(items), 3)

        # check the logo is there
        logo = items[0]
        self.assertIsInstance(logo, Anchor)

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertIsInstance(edit, Switcher)
        self.assertFalse(toolbar.edit_mode)

        # check the logout button
        logout = items[-1]
        self.assertIsInstance(logout, GetButton)
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_staff(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_superuser())
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

        # check the logo is there
        logo = items[0]
        self.assertIsInstance(logo, Anchor)

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertIsInstance(edit, Switcher)
        self.assertFalse(toolbar.edit_mode)

        # check templates
        templates = items[2]
        self.assertIsInstance(templates, List)
        self.assertEqual(len(templates.raw_items), len(get_cms_setting('TEMPLATES')))
        base = reverse('admin:cms_page_change_template', args=(page.pk,))
        for item, template in zip(templates.raw_items, get_cms_setting('TEMPLATES')):
            self.assertEqual(item.url, '%s?template=%s' % (base, template[0]))

        # check page menu
        pagemenu = items[3]
        self.assertIsInstance(pagemenu, List)
        self.assertEqual(len(pagemenu.raw_items), 4)

        overview, addchild, addsibling, delete = pagemenu.raw_items
        self.assertEqual(overview.url, reverse('admin:cms_page_changelist'))
        self.assertEqual(addchild.serialize_url({}, toolbar),
            reverse('admin:cms_page_add') + '?position=last-child&target=%s' % page.pk)
        self.assertEqual(addsibling.serialize_url({}, toolbar),
            reverse('admin:cms_page_add') + '?position=last-child')
        self.assertEqual(delete.serialize_url({}, toolbar),
            reverse('admin:cms_page_delete', args=(page.pk,)))

        # check the admin-menu
        admin = items[4]
        self.assertIsInstance(admin, List)
        self.assertEqual(len(admin.raw_items), 3) # page settings, history and admin
        self.assertIsInstance(admin.raw_items[0], ListItem)
        self.assertIsInstance(admin.raw_items[1], ListItem)
        self.assertIsInstance(admin.raw_items[2], ListItem)

        # check the logout button
        logout = items[-1]
        self.assertIsInstance(logout, GetButton)
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_template_change_permission(self):
        with SettingsOverride(CMS_PERMISSIONS=True):
            page = create_page('test', 'nav_playground.html', 'en', published=True)
            request = self.get_page_request(page, self.get_nonstaff())
            toolbar = CMSToolbar(request)
            items = toolbar.get_items({})
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

        items = toolbar.get_items({})

        # Logo + edit-mode + publish + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 7)

        publish = items[2]
        self.assertIsInstance(publish, GetButton)


    def test_toolbar_no_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_staff(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.get_items({})
        # Logo + edit-mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

    def test_toolbar_no_change_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        user = self.get_staff()
        user.user_permissions.all().delete()
        request = self.get_page_request(page, user, edit=True)
        toolbar = CMSToolbar(request)
        self.assertFalse(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.get_items({})
        # Logo + page-menu + admin-menu + logout
        self.assertEqual(len(items), 4)

