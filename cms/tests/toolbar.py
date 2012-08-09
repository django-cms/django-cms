from __future__ import with_statement
from cms.api import create_page
from cms.cms_toolbar import CMSToolbar
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.toolbar.items import (Anchor, TemplateHTML, Switcher, List, ListItem, 
    GetButton)
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

class ToolbarUserMixin(object):
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
        return staff

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


class ToolbarTests(SettingsOverrideTestCase, ToolbarUserMixin):
    settings_overrides = {'CMS_MODERATOR': False}

    @property
    def request_factory(self):
        return RequestFactory()

    def test_toolbar_no_page_anon(self):
        request = self.request_factory.get('/')
        request.user = self.get_anon()
        request.current_page = None
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        self.assertEqual(len(items), 2) # Logo + login

        # check the logo is there
        logo = items[0]
        self.assertTrue(isinstance(logo, Anchor))

        # check the login form is there
        login = items[1]
        self.assertTrue(isinstance(login, TemplateHTML))
        self.assertEqual(login.template, 'cms/toolbar/items/login.html')

    def test_toolbar_no_page_staff(self):
        request = self.request_factory.get('/')
        request.user = self.get_staff()
        request.current_page = None
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 4)

        # check the logo is there
        logo = items[0]
        self.assertTrue(isinstance(logo, Anchor))

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertTrue(isinstance(edit, Switcher))
        self.assertFalse(toolbar.edit_mode)

        # check the admin-menu
        admin = items[2]
        self.assertTrue(isinstance(admin, List))
        self.assertEqual(len(admin.raw_items), 1) # only the link to main admin
        self.assertTrue(isinstance(admin.raw_items[0], ListItem))

        # check the logout button
        logout = items[3]
        self.assertTrue(isinstance(logout, GetButton))
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_no_page_superuser(self):
        request = self.request_factory.get('/')
        request.user = self.get_superuser()
        request.current_page = None
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 4)

        # check the logo is there
        logo = items[0]
        self.assertTrue(isinstance(logo, Anchor))

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertTrue(isinstance(edit, Switcher))
        self.assertFalse(toolbar.edit_mode)

        # check the admin-menu
        admin = items[2]
        self.assertTrue(isinstance(admin, List))
        self.assertEqual(len(admin.raw_items), 1) # only the link to main admin
        self.assertTrue(isinstance(admin.raw_items[0], ListItem))

        # check the logout button
        logout = items[3]
        self.assertTrue(isinstance(logout, GetButton))
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_anon(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.request_factory.get('/')
        request.user = self.get_anon()
        request.current_page = page
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        self.assertEqual(len(items), 2) # Logo + login

        # check the logo is there
        logo = items[0]
        self.assertTrue(isinstance(logo, Anchor))

        # check the login form is there
        login = items[1]
        self.assertTrue(isinstance(login, TemplateHTML))
        self.assertEqual(login.template, 'cms/toolbar/items/login.html')

    def test_toolbar_staff(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.request_factory.get(page.get_absolute_url())
        request.user = self.get_superuser()
        request.current_page = page
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

        # check templates
        templates = items[2]
        self.assertTrue(isinstance(templates, List))
        self.assertEqual(len(templates.raw_items), len(settings.CMS_TEMPLATES))
        base = reverse('admin:cms_page_change_template', args=(page.pk,))
        for item, template in zip(templates.raw_items, settings.CMS_TEMPLATES):
            self.assertEqual(item.url, '%s?template=%s' % (base, template[0]))

        # normal staff without templates
        request.user = self.get_staff()
        request.session = {}
        toolbar = CMSToolbar(request)

        items = toolbar.get_items({})
        # Logo + edit-mode + page-menu + admin-menu + logout
        self.assertEqual(len(items), 5)
        # check the logo is there
        logo = items[0]
        self.assertTrue(isinstance(logo, Anchor))

        # check the edit-mode switcher is there and the switcher is turned off
        edit = items[1]
        self.assertTrue(isinstance(edit, Switcher))
        self.assertFalse(toolbar.edit_mode)

        # check page menu
        pagemenu = items[2]
        self.assertTrue(isinstance(pagemenu, List))
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
        admin = items[3]
        self.assertTrue(isinstance(admin, List))
        self.assertEqual(len(admin.raw_items), 1) # only the link to main admin
        self.assertTrue(isinstance(admin.raw_items[0], ListItem))

        # check the logout button
        logout = items[4]
        self.assertTrue(isinstance(logout, GetButton))
        self.assertEqual(logout.url, '?cms-toolbar-logout')

    def test_toolbar_template_change_permission(self):
        with SettingsOverride(CMS_PERMISSIONS=True):
            page = create_page('test', 'nav_playground.html', 'en', published=True)
            request = self.request_factory.get(page.get_absolute_url())
            request.user = self.get_staff()
            request.current_page = page
            SessionMiddleware().process_request(request)
            request.session = {}
            toolbar = CMSToolbar(request)
            items = toolbar.get_items({})
            self.assertEqual([item for item in items if item.css_class_suffix == 'templates'], [])
        
    def test_toolbar_markup(self):
        superuser = self.get_superuser()
        create_page("toolbar-page", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        
        with self.login_user_context(superuser):
            response = self.client.get('/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'nav_playground.html')
        self.assertContains(response, '<div id="cms_toolbar"')
        self.assertContains(response, 'cms.placeholders.js')
        self.assertContains(response, 'cms.placeholders.css')

    def test_show_toolbar_to_staff(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        request = self.request_factory.get(page.get_absolute_url())
        request.user = self.get_staff()
        request.current_page = page
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_with_edit(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        request = self.request_factory.get('%s?edit' % page.get_absolute_url())
        request.current_page = page
        request.user = AnonymousUser()
        SessionMiddleware().process_request(request)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_without_edit(self):
        superuser = self.get_superuser()
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           created_by=superuser, published=True)
        request = self.request_factory.get(page.get_absolute_url())
        request.current_page = page
        request.user = AnonymousUser()
        SessionMiddleware().process_request(request)
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)
        

class ToolbarModeratorTests(SettingsOverrideTestCase, ToolbarUserMixin):
    settings_overrides = {'CMS_MODERATOR': True}

    def setUp(self):
        self.request_factory = RequestFactory()

    def test_toolbar_moderate_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.request_factory.get(page.get_absolute_url() + '?edit')
        request.user = self.get_staff()
        request.current_page = page
        request.session = {}
        toolbar = CMSToolbar(request)

        self.assertTrue(toolbar.edit_mode)

        items = toolbar.get_items({})

        # Logo + edit-mode + moderate + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

        moderate = items[2]
        self.assertTrue(isinstance(moderate, GetButton))


class ToolbarNoModeratorTests(SettingsOverrideTestCase, ToolbarUserMixin):
    settings_overrides = {'CMS_MODERATOR': False}

    def setUp(self):
        self.request_factory = RequestFactory()

    def test_toolbar_no_moderate_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.request_factory.get(page.get_absolute_url() + '?edit')
        request.user = self.get_staff()
        request.session = {}
        request.current_page = page
        toolbar = CMSToolbar(request)

        self.assertTrue(toolbar.edit_mode)

        items = toolbar.get_items({})
        # Logo + edit-mode + page-menu + admin-menu + logout
        self.assertEqual(len(items), 5)

