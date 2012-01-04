# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import (create_page, publish_page, approve_page, add_plugin, 
    create_page_user, assign_user_to_page)
from cms.models import Page, CMSPlugin
from cms.models.moderatormodels import (ACCESS_DESCENDANTS, 
    ACCESS_PAGE_AND_DESCENDANTS)
from cms.models.permissionmodels import PagePermission, GlobalPagePermission
from cms.test_utils.testcases import (URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_REMOVE, 
    SettingsOverrideTestCase, URL_CMS_PLUGIN_ADD, CMSTestCase)
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.page_resolver import get_page_from_path
from cms.utils.permissions import has_generic_permission
from django.contrib.auth.models import User, Permission, AnonymousUser, Group
from django.contrib.sites.models import Site
from django.core.management import call_command


class PermissionModeratorTests(SettingsOverrideTestCase):
    """Permissions and moderator together
    
    Fixtures contains 3 users and 1 published page and some other stuff
    
    Users:
        1. `super`: superuser
        2. `master`: user with permissions to all applications
        3. `slave`: user assigned to page `slave-home`
    
    Pages:
        1. `home`:
            - published page
            - master can do anything on its subpages, but not on home!
            
        2. `master`:
            - published page
            - crated by super
            - `master` can do anything on it and its descendants
            - subpages:
        
        3.       `slave-home`:
                    - not published
                    - assigned slave user which can add/change/delete/
                      move/publish/moderate this page and its descendants
                    - `master` user want to moderate this page and all descendants
                    
        4. `pageA`:
            - created by super
            - master can add/change/delete on it and descendants 
    """
    settings_overrides = {
        'CMS_PERMISSION': True,
        'CMS_MODERATOR': True,
    }
    
    def setUp(self):
        # create super user
        self.user_super = User(username="super", is_staff=True, is_active=True, 
            is_superuser=True)
        self.user_super.set_password("super")
        self.user_super.save()
        # create staff user
        self.user_staff = User(username="staff", is_staff=True, is_active=True)
        self.user_staff.set_password("staff")
        self.user_staff.save()
        
        with self.login_user_context(self.user_super):
            
            self._home_page = create_page("home", "nav_playground.html", "en",
                                         created_by=self.user_super)
        
            # master page & master user
            
            self._master_page = create_page("master", "nav_playground.html", "en")
            
            # create master user
            master = User(username="master", email="master@django-cms.org", is_staff=True, is_active=True)
            master.set_password('master')
            master.save()
            master.user_permissions.add(Permission.objects.get(codename='add_text'))
            master.user_permissions.add(Permission.objects.get(codename='delete_text'))
            master.user_permissions.add(Permission.objects.get(codename='change_text'))
            
            self.user_master = create_page_user(self.user_super, master, grant_all=True)
            # create non global, non staff user
            self.user_non_global = User(username="nonglobal", is_active=True)
            self.user_non_global.set_password("nonglobal")
            self.user_non_global.save()
            
            # assign master user under home page
            assign_user_to_page(self.home_page, self.user_master,
                                grant_on=ACCESS_DESCENDANTS, grant_all=True)
            
            # and to master page
            assign_user_to_page(self.master_page, self.user_master,
                                grant_on=ACCESS_PAGE_AND_DESCENDANTS, grant_all=True)
            
            # slave page & slave user
            
            self._slave_page = create_page("slave-home", "nav_playground.html", "en",
                              parent=self.master_page, created_by=self.user_super)
        
            slave = User(username='slave', email='slave@django-cms.org', is_staff=True)
            slave.set_password('slave')
            slave.save()
            slave.user_permissions.add(Permission.objects.get(codename='add_text'))
            slave.user_permissions.add(Permission.objects.get(codename='delete_text'))
            slave.user_permissions.add(Permission.objects.get(codename='change_text'))
            
            self.user_slave = create_page_user(self.user_super, slave,  can_add_page=True,
                                        can_change_page=True, can_delete_page=True)
            
            assign_user_to_page(self.slave_page, self.user_slave, grant_all=True)
    
            # create page_b
            page_b = create_page("pageB", "nav_playground.html", "en", created_by=self.user_super)
            # Normal user
            normal = User(username='normal', email='normal@django-cms.org', is_active=True)
            normal.set_password('normal')
            normal.save()
            self.user_normal = create_page_user(self.user_master, normal)
            # it's allowed for the normal user to view the page
            assign_user_to_page(page_b, self.user_normal, can_view=True)
            self.user_normal = self.reload(self.user_normal)
            # create page_a - sample page from master
            
            page_a = create_page("pageA", "nav_playground.html", "en",
                                 created_by=self.user_super)
            assign_user_to_page(page_a, self.user_master, 
                can_add=True, can_change=True, can_delete=True, can_publish=True, 
                can_move_page=True, can_moderate=True)

            # publish after creating all drafts
            publish_page(self.home_page, self.user_super)
            
            publish_page(self.master_page, self.user_super)
            
            self.page_b = publish_page(page_b, self.user_super)
            # logg in as master, and request moderation for slave page and descendants
            self.request_moderation(self.slave_page, 7)
    
    @property
    def master_page(self):
        return self.reload(self._master_page)
    
    @property
    def slave_page(self):
        return self.reload(self._slave_page)
    
    @property
    def home_page(self):
        return self.reload(self._home_page)
    
    def _add_plugin(self, user, page):
        """
        Add a plugin using the test client to check for permissions.
        """
        with self.login_user_context(user):
            placeholder = page.placeholders.all()[0]
            post_data = {
                'language': 'en',
                'page_id': page.pk,
                'placeholder': placeholder.pk,
                'plugin_type': 'TextPlugin'
            }
            url = URL_CMS_PLUGIN_ADD % page.pk
            response = self.client.post(url, post_data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.isdigit())
            return response.content

    def test_super_can_add_page_to_root(self):
        with self.login_user_context(self.user_super):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 200)
    
    def test_master_can_add_page_to_root(self):
        with self.login_user_context(self.user_master):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 403)
        
    def test_slave_can_add_page_to_root(self):
        with self.login_user_context(self.user_slave):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 403)
    
    def test_moderation_on_slave_home(self):
        self.assertEqual(self.slave_page.get_moderator_queryset().count(), 1)
    
    def test_slave_can_add_page_under_slave_home(self):
        with self.login_user_context(self.user_slave):
            # move to admin.py?
            # url = URL_CMS_PAGE_ADD + "?target=%d&position=last-child" % slave_page.pk
            
            # can he even access it over get?
            # response = self.client.get(url)
            # self.assertEqual(response.status_code, 200)
            
            # add page
            page = create_page("page", "nav_playground.html", "en",
                               parent=self.slave_page, created_by=self.user_slave)
            # adds user_slave as page moderator for this page
            # public model shouldn't be available yet, because of the moderation
            # removed test cases since Title object does not inherit from Publisher anymore
            #self.assertObjectExist(Title.objects, slug=page_data['slug'])
            #self.assertObjectDoesNotExist(Title.objects.public(), slug=page_data['slug'])
            
            # moderators and approvement ok?
            self.assertEqual(page.get_moderator_queryset().count(), 1)
            self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
            
            # must not have public object yet
            self.assertFalse(page.publisher_public)
    
            self.assertTrue(has_generic_permission(page.pk, self.user_slave, "publish", 1))
    
            # publish as slave, published as user_master before 
            publish_page(page, self.user_slave)
            
            # user_slave is moderator for this page
            # approve / publish as user_slave
            # user master should be able to approve aswell
            page = approve_page(page, self.user_slave)

    def test_page_added_by_slave_can_be_published_approved_by_user_master(self):
        # add page
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page, created_by=self.user_slave)
        # same as test_slave_can_add_page_under_slave_home        
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
        
        # must not have public object yet
        self.assertFalse(page.publisher_public)
        
        self.assertTrue(has_generic_permission(page.pk, self.user_master, "publish", page.site.pk))
        # should be True user_master should have publish permissions for childred aswell
        # don't test for published since publishing must be approved
        publish_page(page, self.user_master)
        
        # user_master is moderator for top level page / but can't approve descendants?
        # approve / publish as user_master
        # user master should be able to approve descendants
        page = approve_page(page, self.user_master)    
        
    def test_super_can_add_plugin(self):
        self._add_plugin(self.user_super, page=self.slave_page)
    
    def test_master_can_add_plugin(self):
        self._add_plugin(self.user_master, page=self.slave_page)
    
    def test_slave_can_add_plugin(self):
        self._add_plugin(self.user_slave, page=self.slave_page)
    
    def test_same_order(self):
        # create 4 pages
        slugs = []
        for i in range(0, 4):
            page = create_page("page", "nav_playground.html", "en",
                               parent=self.home_page)
            slug = page.title_set.drafts()[0].slug
            slugs.append(slug)
        
        # approve last 2 pages in reverse order
        for slug in reversed(slugs[2:]):
            page = self.assertObjectExist(Page.objects.drafts(), title_set__slug=slug)
            page = publish_page(page, self.user_master, True)
            self.check_published_page_attributes(page)
    
    def test_create_copy_publish(self):
        # create new page to copy
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page)
        
        # copy it under home page...
        # TODO: Use page.copy_page here
        with self.login_user_context(self.user_master):
            copied_page = self.copy_page(page, self.home_page)
        
        page = publish_page(copied_page, self.user_master, True)
        self.check_published_page_attributes(page)
    
    
    def test_create_publish_copy(self):
        # create new page to copy
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.home_page)
        
        page = publish_page(page, self.user_master, True)
        
        # copy it under master page...
        # TODO: Use page.copy_page here
        with self.login_user_context(self.user_master):
            copied_page = self.copy_page(page, self.master_page)
        
        self.check_published_page_attributes(page)
        copied_page = publish_page(copied_page, self.user_master, True)
        self.check_published_page_attributes(copied_page)
        
        
    def test_subtree_needs_approvement(self):
        # create page under slave_page
        page = create_page("parent", "nav_playground.html", "en",
                           parent=self.home_page)
        self.assertFalse(page.publisher_public)
        
        # create subpage uner page
        subpage = create_page("subpage", "nav_playground.html", "en", parent=page)
        self.assertFalse(subpage.publisher_public)
        
        # publish both of them in reverse order 
        subpage = publish_page(subpage, self.user_master, True) 
        
        # subpage should not be published, because parent is not published 
        # yet, should be marked as `publish when parent`
        self.assertFalse(subpage.publisher_public) 
        
        # pagemoderator state must be set
        self.assertEqual(subpage.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish page (parent of subage), so subpage must be published also
        page = publish_page(page, self.user_master, True)
        self.assertNotEqual(page.publisher_public, None)
        
        # reload subpage, it was probably changed
        subpage = self.reload_page(subpage)
        
        # parent was published, so subpage must be also published..
        self.assertNotEqual(subpage.publisher_public, None) 
        
        #check attributes
        self.check_published_page_attributes(page)
        self.check_published_page_attributes(subpage)


    def test_subtree_with_super(self):
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        self.assertFalse(page.publisher_public)
        
        # create subpage under page
        subpage = create_page("subpage", "nav_playground.html", "en",
                              parent=page)
        self.assertFalse(subpage.publisher_public)
        
        # tree id must be the same
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        # publish both of them  
        page = self.reload(page)
        page = publish_page(page, self.user_super, True)
        # reload subpage, there were an tree_id change
        subpage = self.reload_page(subpage)
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        subpage = publish_page(subpage, self.user_super, True)
        # tree id must stay the same
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        # published pages must also have the same tree_id
        self.assertEqual(page.publisher_public.tree_id, subpage.publisher_public.tree_id)
        
        #check attributes
        self.check_published_page_attributes(page) 
        self.check_published_page_attributes(subpage)
        
        
    def test_super_add_page_to_root(self):
        """Create page which is not under moderation in root, and check if 
        some properties are correct.
        """
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        
        # public must not exist
        self.assertFalse(page.publisher_public)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
    
    
    def test_moderator_flags(self):
        """Add page under slave_home and check its flag
        """
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
        
        # check publish box
        page = publish_page(page, self.user_slave)
        
        # page should request approvement now
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # approve it by master

        # approve this page - but it doesn't get published yet, because 
        # slave home is not published
        page = approve_page(page, self.user_master)
        
        # public page must not exist because of parent
        self.assertFalse(page.publisher_public)
        
        # waiting for parents
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish slave page
        slave_page = publish_page(self.slave_page, self.user_master)
        
        self.assertFalse(page.publisher_public)
        self.assertFalse(slave_page.publisher_public)
        
        # they must be approved first
        slave_page = approve_page(slave_page, self.user_master)
        
        # master is approved
        self.assertEqual(slave_page.moderator_state, Page.MODERATOR_APPROVED)
        
        # reload page
        page = self.reload_page(page)
        
        # page must be approved also now
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)
        
    def test_plugins_get_published(self):
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", "en", body="test")
        # public must not exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        publish_page(page, self.user_super, True)
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

    def test_remove_plugin_page_under_moderation(self):
        # login as slave and create page
        page = create_page("page", "nav_playground.html", "en", parent=self.slave_page)
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        
        # add plugin
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, "TextPlugin", "en", body="test")
        
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)

        # publish page
        page = self.reload(page)
        page = publish_page(page, self.user_slave)
        
        # only the draft plugin should exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        
        # page should require approval
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # master approves and publishes the page
        # first approve slave-home
        slave_page = self.reload(self.slave_page)
        publish_page(slave_page, self.user_master, approve=True)
        page = self.reload(page)
        page = publish_page(page, self.user_master, approve=True)
        
        # draft and public plugins should now exist
        self.assertEqual(CMSPlugin.objects.all().count(), 2)
        
        # login as slave and delete the plugin - should require moderation
        with self.login_user_context(self.user_slave):
            plugin_data = {
                'plugin_id': plugin.pk
            }
            remove_url = URL_CMS_PLUGIN_REMOVE
            response = self.client.post(remove_url, plugin_data)
            self.assertEquals(response.status_code, 200)
    
            # there should only be a public plugin - since the draft has been deleted
            self.assertEquals(CMSPlugin.objects.all().count(), 1)
            
            # reload the page as it's moderator value should have been set in pageadmin.remove_plugin
            self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)
            page = self.reload_page(page)
    
            self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
    
            # login as super user and approve/publish the page
            page = publish_page(page, self.user_super, approve=True)
            self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)
    
            # there should now be 0 plugins
            self.assertEquals(CMSPlugin.objects.all().count(), 0)

    def test_superuser_can_view(self):
        with self.login_user_context(self.user_super):
            response = self.client.get("/en/pageb/")
            self.assertEqual(response.status_code, 200)

    def test_staff_can_view(self):
        with self.login_user_context(self.user_staff):
            response = self.client.get("/en/pageb/")
            self.assertEqual(response.status_code, 200)

    def test_user_normal_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        with self.login_user_context(self.user_normal):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        with self.login_user_context(self.user_non_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
        # non logged in user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_globalpermission(self):
        # Global user
        with self.login_user_context(self.user_super):
            user_global = User(username="global", is_active=True)
            user_global.set_password("global")
            user_global.save()
            user_global = create_page_user(user_global, user_global)
            user_global.is_staff = False
            user_global.save() # Prevent is_staff permission
            global_page = create_page("global", "nav_playground.html", "en",
                                      published=True)
            global_page = publish_page(global_page, user_global, approve=True)
            # it's allowed for the normal user to view the page
            assign_user_to_page(global_page, user_global,
                global_permission=True, can_view=True)
        
        url = global_page.get_absolute_url('en')

        with self.login_user_context(user_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        with self.login_user_context(self.user_non_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_anonymous_user_public_for_all(self):
        url = self.page_b.get_absolute_url('en')
        with SettingsOverride(CMS_PUBLIC_FOR='all'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_anonymous_user_public_for_none(self):
        # default of when to show pages to anonymous user doesn't take
        # global permissions into account
        url = self.page_b.get_absolute_url('en')
        with SettingsOverride(CMS_PUBLIC_FOR=None):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            

class PatricksMoveTest(SettingsOverrideTestCase):
    """
    Fixtures contains 3 users and 1 published page and some other stuff
    
    Users:
        1. `super`: superuser
        2. `master`: user with permissions to all applications
        3. `slave`: user assigned to page `slave-home`
    
    Pages:
        1. `home`:
            - published page
            - master can do anything on its subpages, but not on home!
            
        2. `master`:
            - published page
            - crated by super
            - `master` can do anything on it and its descendants
            - subpages:
        
        3.       `slave-home`:
                    - not published
                    - assigned slave user which can add/change/delete/
                      move/publish/moderate this page and its descendants
                    - `master` user want to moderate this page and all descendants
                    
        4. `pageA`:
            - created by super
            - master can add/change/delete on it and descendants 
    """
    settings_overrides = {
        'CMS_PERMISSION': True,
        'CMS_MODERATOR': True,
    }
    
    def setUp(self):
        # create super user
        self.user_super = User(username="super", is_staff=True, is_active=True, 
            is_superuser=True)
        self.user_super.set_password("super")
        self.user_super.save()
        with self.login_user_context(self.user_super):
        
            self._home_page = create_page("home", "nav_playground.html", "en",
                                         created_by=self.user_super)
            
            # master page & master user
            
            self._master_page = create_page("master", "nav_playground.html", "en")
    
            # create master user
            master = User.objects.create(username="master", email="master@django-cms.org", password="master")
            self.user_master = create_page_user(self.user_super, master, grant_all=True)
            
            # assign master user under home page
            assign_user_to_page(self.home_page, self.user_master,
                                grant_on=ACCESS_DESCENDANTS, grant_all=True)
            
            # and to master page
            assign_user_to_page(self.master_page, self.user_master, grant_all=True)
            
            # slave page & slave user
            
            self._slave_page = create_page("slave-home", "nav_playground.html", "en",
                              parent=self.master_page, created_by=self.user_super)
            slave = User(username='slave', email='slave@django-cms.org', is_staff=True, is_active=True)
            slave.set_password('slave')
            slave.save()
            self.user_slave = create_page_user(self.user_super, slave,  can_add_page=True,
                                        can_change_page=True, can_delete_page=True)
            
            assign_user_to_page(self.slave_page, self.user_slave, grant_all=True)
            
            # create page_a - sample page from master
            
            page_a = create_page("pageA", "nav_playground.html", "en",
                                 created_by=self.user_super)
            assign_user_to_page(page_a, self.user_master, 
                can_add=True, can_change=True, can_delete=True, can_publish=True, 
                can_move_page=True, can_moderate=True)
            
            # publish after creating all drafts
            publish_page(self.home_page, self.user_super)
            publish_page(self.master_page, self.user_super)
            # logg in as master, and request moderation for slave page and descendants
            self.request_moderation(self.slave_page, 7)
        
        with self.login_user_context(self.user_slave):
        
            # all of them are under moderation... 
            self._pa = create_page("pa", "nav_playground.html", "en", parent=self.slave_page)
            self._pb = create_page("pb", "nav_playground.html", "en", parent=self.pa, position="right")
            self._pc = create_page("pc", "nav_playground.html", "en", parent=self.pb, position="right")
            
            self._pd = create_page("pd", "nav_playground.html", "en", parent=self.pb)
            self._pe = create_page("pe", "nav_playground.html", "en", parent=self.pd, position="right")
            
            self._pf = create_page("pf", "nav_playground.html", "en", parent=self.pe)
            self._pg = create_page("pg", "nav_playground.html", "en", parent=self.pf, position="right")
            self._ph = create_page("ph", "nav_playground.html", "en", parent=self.pf, position="right")
            
            self.assertFalse(self.pg.publisher_public)
            
            # login as master for approval
            publish_page(self.slave_page, self.user_master, approve=True)
            
            # publish and approve them all
            publish_page(self.pa, self.user_master, approve=True)
            publish_page(self.pb, self.user_master, approve=True)
            publish_page(self.pc, self.user_master, approve=True)
            publish_page(self.pd, self.user_master, approve=True)
            publish_page(self.pe, self.user_master, approve=True)
            publish_page(self.pf, self.user_master, approve=True)
            publish_page(self.pg, self.user_master, approve=True)
            publish_page(self.ph, self.user_master, approve=True)
        
    @property
    def master_page(self):
        return self.reload(self._master_page)
    
    @property
    def slave_page(self):
        return self.reload(self._slave_page)
    
    @property
    def home_page(self):
        return self.reload(self._home_page)
    
    @property
    def pa(self):
        return self.reload(self._pa)
    
    @property
    def pb(self):
        return self.reload(self._pb)
    
    @property
    def pc(self):
        return self.reload(self._pc)
    
    @property
    def pd(self):
        return self.reload(self._pd)
    
    @property
    def pe(self):
        return self.reload(self._pe)
    
    @property
    def pf(self):
        return self.reload(self._pf)
    
    @property
    def pg(self):
        return self.reload(self._pg)
    
    @property
    def ph(self):
        return self.reload(self._ph)
        
    def test_patricks_move(self):
        """
        
        Tests permmod when moving trees of pages.

        1. build following tree (master node is approved and published)
        
                 slave-home
                /    |    \
               A     B     C
                   /  \     
                  D    E     
                    /  |  \ 
                   F   G   H               

        2. perform move oparations:
            1. move G under C
            2. move E under G
            
                 slave-home
                /    |    \
               A     B     C
                   /        \
                  D          G
                              \   
                               E
                             /   \
                            F     H       
        
        3. approve nodes in following order:
            1. approve H
            2. approve G
            3. approve E
            4. approve F
        """
        # TODO: this takes 5 seconds to run on my MBP. That's TOO LONG!
        
        # perform movings under slave...
        user_master = User.objects.get(username='master')
        self.move_page(self.pg, self.pc)
        # We have to reload pe when using mptt >= 0.4.2, 
        # so that mptt realized that pg is no longer a child of pe
        self.move_page(self.pe, self.pg)
        
        # check urls - they should stay them same, there wasn't approved yet
        self.assertEqual(
            self.pg.publisher_public.get_absolute_url(), 
            u'%smaster/slave-home/pb/pe/pg/' % self.get_pages_root()
        )
        self.assertEqual(
            self.ph.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pb/pe/ph/' % self.get_pages_root()
        )
        
        # pg & pe should require approval
        self.assertEqual(self.pg.requires_approvement(), True)
        self.assertEqual(self.pe.requires_approvement(), True)
        self.assertEqual(self.ph.requires_approvement(), False)
        
        # login as master, and approve moves
        approve_page(self.pg, user_master)
        approve_page(self.pe, user_master)
        approve_page(self.ph, user_master)
        approve_page(self.pf, user_master)
        
        # public parent check after move
        self.assertEqual(self.pg.publisher_public.parent.pk, self.pc.publisher_public_id)
        self.assertEqual(self.pe.publisher_public.parent.pk, self.pg.publisher_public_id)
        self.assertEqual(self.ph.publisher_public.parent.pk, self.pe.publisher_public_id)
        
        # check if urls are correct after move
        self.assertEqual(
            self.pg.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pc/pg/' % self.get_pages_root()
        )
        self.assertEqual(
            self.ph.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pc/pg/pe/ph/' % self.get_pages_root()
        )


class ModeratorSwitchCommandTest(CMSTestCase):
    def test_switch_moderator_on(self):
        with SettingsOverride(CMS_MODERATOR=False):
            page1 = create_page('page', 'nav_playground.html', 'en', published=True)
        with SettingsOverride(CMS_MODERATOR=True):
            call_command('cms', 'moderator', 'on')
            page2 = get_page_from_path(page1.get_absolute_url().strip('/'))
        self.assertEqual(page1.get_absolute_url(), page2.get_absolute_url())
        
    def test_switch_moderator_off(self):
        with SettingsOverride(CMS_MODERATOR=True):
            page1 = create_page('page', 'nav_playground.html', 'en', published=True)
        with SettingsOverride(CMS_MODERATOR=False):
            page2 = get_page_from_path(page1.get_absolute_url().strip('/'))
        self.assertEqual(page1.get_absolute_url(), page2.get_absolute_url())


class ViewPermissionTests(SettingsOverrideTestCase):
    settings_overrides = {
        'CMS_MODERATOR': False,
        'CMS_PERMISSION': True,
        'CMS_PUBLIC_FOR': 'all',
    }

    
    def get_request(self, user=None):
        attrs = {
            'user': user or AnonymousUser(),
            'REQUEST': {},
            'session': {},
        }
        return type('Request', (object,), attrs)
    
    def test_public_for_all_staff(self):
        request = self.get_request()
        request.user.is_staff = True
        page = Page()
        page.pk = 1
        self.assertTrue(page.has_view_permission(request))

    def test_public_for_all_staff_assert_num_queries(self):
        request = self.get_request()
        request.user.is_staff = True
        page = Page()
        page.pk = 1
        with self.assertNumQueries(0):
            page.has_view_permission(request)

    def test_public_for_all(self):
        user = User.objects.create_user('user', 'user@domain.com', 'user')
        request = self.get_request(user)
        page = Page()
        page.pk = 1
        page.level = 0
        page.tree_id = 1
        self.assertTrue(page.has_view_permission(request))

    def test_public_for_all_num_queries(self):
        user = User.objects.create_user('user', 'user@domain.com', 'user')
        request = self.get_request(user)
        site = Site()
        site.pk = 1
        page = Page()
        page.pk = 1
        page.level = 0
        page.tree_id = 1
        with self.assertNumQueries(3):
            """
            The queries are:
            The current Site
            PagePermission query for affected pages
            GlobalpagePermission query for user
            """
            page.has_view_permission(request)
    
    def test_unauthed(self):
        request = self.get_request()
        page = Page()
        page.pk = 1
        page.level = 0
        page.tree_id = 1
        self.assertTrue(page.has_view_permission(request))
        
    def test_unauthed_num_queries(self):
        request = self.get_request()
        site = Site()
        site.pk = 1
        page = Page()
        page.pk = 1
        page.level = 0
        page.tree_id = 1
        with self.assertNumQueries(1):
            """
            The query is:
            PagePermission query for affected pages
            """
            page.has_view_permission(request)
    
    def test_authed_basic_perm(self):
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            user = User.objects.create_user('user', 'user@domain.com', 'user')
            user.user_permissions.add(Permission.objects.get(codename='view_page'))
            request = self.get_request(user)
            page = Page()
            page.pk = 1
            page.level = 0
            page.tree_id = 1
            self.assertTrue(page.has_view_permission(request))
    
    def test_authed_basic_perm_num_queries(self):
        site = Site()
        site.pk = 1
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            user = User.objects.create_user('user', 'user@domain.com', 'user')
            user.user_permissions.add(Permission.objects.get(codename='view_page'))
            request = self.get_request(user)
            page = Page()
            page.pk = 1
            page.level = 0
            page.tree_id = 1
            with self.assertNumQueries(5):
                """
                The queries are:
                The site
                PagePermission query for affected pages
                GlobalpagePermission query for user
                Generic django permission lookup
                content type lookup by permission lookup
                """
                page.has_view_permission(request)
    
    def test_authed_no_access(self):
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            user = User.objects.create_user('user', 'user@domain.com', 'user')
            request = self.get_request(user)
            page = Page()
            page.pk = 1
            page.level = 0
            page.tree_id = 1
            self.assertFalse(page.has_view_permission(request))
    
    def test_unauthed_no_access(self):
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            request = self.get_request()
            page = Page()
            page.pk = 1
            page.level = 0
            page.tree_id = 1
            self.assertFalse(page.has_view_permission(request))
        
    def test_unauthed_no_access_num_queries(self):
        site = Site()
        site.pk = 1
        request = self.get_request()
        page = Page()
        page.pk = 1
        page.level = 0
        page.tree_id = 1
        with self.assertNumQueries(1):
            page.has_view_permission(request)
    
    def test_page_permissions(self):
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            user = User.objects.create_user('user', 'user@domain.com', 'user')
            request = self.get_request(user)
            page = create_page('A', 'nav_playground.html', 'en')
            PagePermission.objects.create(can_view=True, user=user, page=page)
            self.assertTrue(page.has_view_permission(request))
    
    def test_page_permissions_view_groups(self):
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            user = User.objects.create_user('user', 'user@domain.com', 'user')
            group = Group.objects.create(name='testgroup')
            group.user_set.add(user)
            request = self.get_request(user)
            page = create_page('A', 'nav_playground.html', 'en')
            PagePermission.objects.create(can_view=True, group=group, page=page)
            self.assertTrue(page.has_view_permission(request))
            
    def test_global_permission(self):
        with SettingsOverride(CMS_PUBLIC_FOR='staff'):
            user = User.objects.create_user('user', 'user@domain.com', 'user')
            GlobalPagePermission.objects.create(can_view=True, user=user)
            request = self.get_request(user)
            page = Page()
            page.pk = 1
            page.level = 0
            page.tree_id = 1
            self.assertTrue(page.has_view_permission(request))
