# -*- coding: utf-8 -*-
from __future__ import with_statement
import urllib
from cms.api import (create_page, publish_page, add_plugin,
                     create_page_user, assign_user_to_page)
from cms.models import Page, CMSPlugin, Title
from cms.models.permissionmodels import (ACCESS_DESCENDANTS,
                                        ACCESS_PAGE_AND_DESCENDANTS)
from cms.models.permissionmodels import PagePermission, GlobalPagePermission
from cms.test_utils.testcases import (URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_REMOVE, 
    SettingsOverrideTestCase, URL_CMS_PLUGIN_ADD, CMSTestCase)
from cms.test_utils.util.context_managers import SettingsOverride
from cms.utils.i18n import force_language
from cms.utils.page_resolver import get_page_from_path
from cms.utils.permissions import has_generic_permission

from django.contrib.auth.models import User, Permission, AnonymousUser, Group
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db.models import Q


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
            - created by super
            - `master` can do anything on it and its descendants
            - subpages:
        
        3.       `slave-home`:
                    - not published
                    - assigned slave user which can add/change/delete/
                      move/publish this page and its descendants
                    - `master` user want to moderate this page and all descendants
                    
        4. `pageA`:
            - created by super
            - master can add/change/delete on it and descendants
    """
    #TODO: Split this test case into one that tests publish functionality, and
    #TODO: one that tests permission inheritance. This is too complex.
    settings_overrides = {
        'CMS_PERMISSION': True,
    }

    def _create_user(self, username, is_staff=True, is_superuser=False):
        user = User(username=username, email=username+'@django-cms.org',
                    is_staff=is_staff, is_active=True, is_superuser=is_superuser)
        user.set_password(username)
        user.save()
        if is_staff and not is_superuser:
            user.user_permissions.add(Permission.objects.get(codename='add_text'))
            user.user_permissions.add(Permission.objects.get(codename='delete_text'))
            user.user_permissions.add(Permission.objects.get(codename='change_text'))
            user.user_permissions.add(Permission.objects.get(codename='publish_page'))

            user.user_permissions.add(Permission.objects.get(codename='add_page'))
            user.user_permissions.add(Permission.objects.get(codename='change_page'))
            user.user_permissions.add(Permission.objects.get(codename='delete_page'))
        return user

    def setUp(self):
        # create super user
        self.user_super = self._create_user("super", is_superuser=True)
        self.user_staff = self._create_user("staff")
        self.user_master = self._create_user("master")
        self.user_slave = self._create_user("slave")
        self.user_normal = self._create_user("normal", is_staff=False)
        self.user_normal.user_permissions.add(
            Permission.objects.get(codename='publish_page'))

        with self.login_user_context(self.user_super):
            
            self.home_page = create_page("home", "nav_playground.html", "en",
                                         created_by=self.user_super)
        
            # master page & master user
            
            self.master_page = create_page("master", "nav_playground.html", "en")
            
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
            
            self.slave_page = create_page("slave-home", "nav_playground.html", "en",
                              parent=self.master_page, created_by=self.user_super)

            assign_user_to_page(self.slave_page, self.user_slave, grant_all=True)
    
            # create page_b
            page_b = create_page("pageB", "nav_playground.html", "en", created_by=self.user_super)
            # Normal user

            # it's allowed for the normal user to view the page
            assign_user_to_page(page_b, self.user_normal, can_view=True)

            # create page_a - sample page from master
            
            page_a = create_page("pageA", "nav_playground.html", "en",
                                 created_by=self.user_super)
            assign_user_to_page(page_a, self.user_master, 
                can_add=True, can_change=True, can_delete=True, can_publish=True, 
                can_move_page=True)

            # publish after creating all drafts
            publish_page(self.home_page, self.user_super)
            
            publish_page(self.master_page, self.user_super)
            
            self.page_b = publish_page(page_b, self.user_super)

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
    
    def test_master_cannot_add_page_to_root(self):
        with self.login_user_context(self.user_master):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 403)
        
    def test_slave_cannot_add_page_to_root(self):
        with self.login_user_context(self.user_slave):
            response = self.client.get(URL_CMS_PAGE_ADD)
            self.assertEqual(response.status_code, 403)
    
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
            # moderators and approval ok?

            # must not have public object yet
            self.assertFalse(page.publisher_public)

            self.assertObjectExist(Title.objects, slug="page")
            self.assertObjectDoesNotExist(Title.objects.public(), slug="page")

            self.assertTrue(has_generic_permission(page.pk, self.user_slave, "publish", 1))
    
            # publish as slave, published as user_master before 
            publish_page(page, self.user_slave)
            
            # user_slave is moderator for this page
            # approve / publish as user_slave
            # user master should be able to approve as well

    def test_page_added_by_slave_can_be_published_by_user_master(self):
        # add page
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page, created_by=self.user_slave)
        # same as test_slave_can_add_page_under_slave_home        

        # must not have public object yet
        self.assertFalse(page.publisher_public)
        
        self.assertTrue(has_generic_permission(page.pk, self.user_master, "publish", page.site.pk))
        # should be True user_master should have publish permissions for children as well
        publish_page(page, self.user_master)
        self.assertTrue(page.published)
        # user_master is moderator for top level page / but can't approve descendants?
        # approve / publish as user_master
        # user master should be able to approve descendants

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
            page = publish_page(page, self.user_master)
            self.check_published_page_attributes(page)
    
    def test_create_copy_publish(self):
        # create new page to copy
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page)
        
        # copy it under home page...
        # TODO: Use page.copy_page here
        with self.login_user_context(self.user_master):
            copied_page = self.copy_page(page, self.home_page)
        
        page = publish_page(copied_page, self.user_master)
        self.check_published_page_attributes(page)
    
    
    def test_create_publish_copy(self):
        # create new page to copy
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.home_page)
        
        page = publish_page(page, self.user_master)
        
        # copy it under master page...
        # TODO: Use page.copy_page here
        with self.login_user_context(self.user_master):
            copied_page = self.copy_page(page, self.master_page)
        
        self.check_published_page_attributes(page)
        copied_page = publish_page(copied_page, self.user_master)
        self.check_published_page_attributes(copied_page)
        
    def test_subtree_needs_approval(self):
        # create page under slave_page
        page = create_page("parent", "nav_playground.html", "en",
                           parent=self.home_page)
        self.assertFalse(page.publisher_public)
        
        # create subpage under page
        subpage = create_page("subpage", "nav_playground.html", "en", parent=page)
        self.assertFalse(subpage.publisher_public)
        
        # publish both of them in reverse order 
        subpage = publish_page(subpage, self.user_master)
        
        # subpage should not be published, because parent is not published 
        # yet, should be marked as `publish when parent`
        self.assertFalse(subpage.publisher_public) 

        # publish page (parent of subage), so subpage must be published also
        page = publish_page(page, self.user_master)
        self.assertNotEqual(page.publisher_public, None)
        
        # reload subpage, it was probably changed
        subpage = self.reload(subpage)
        
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
        page = publish_page(page, self.user_super)
        # reload subpage, there were an tree_id change
        subpage = self.reload(subpage)
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        subpage = publish_page(subpage, self.user_super)
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

    def test_moderator_flags(self):
        """Add page under slave_home and check its flag
        """
        page = create_page("page", "nav_playground.html", "en",
                           parent=self.slave_page)

        # No public version
        self.assertIsNone(page.publisher_public)
        self.assertFalse(page.published)

        # check publish box
        page = publish_page(page, self.user_slave)

        # public page must not exist because of parent
        self.assertFalse(page.publisher_public)
        
        # waiting for parents
        self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_PENDING)
        
        # publish slave page
        slave_page = publish_page(self.slave_page, self.user_master)
        
        self.assertFalse(page.publisher_public)
        self.assertTrue(slave_page.publisher_public)

        # reload page
        page = self.reload(page)

    def test_plugins_get_published(self):
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", "en", body="test")
        # public must not exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        publish_page(page, self.user_super)
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

    def test_remove_plugin_page_under_moderation(self):
        # login as slave and create page
        page = create_page("page", "nav_playground.html", "en", parent=self.slave_page)

        # add plugin
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, "TextPlugin", "en", body="test")

        # publish page
        page = self.reload(page)
        page = publish_page(page, self.user_slave)
        
        # only the draft plugin should exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        
        # page should require approval
        self.assertEqual(page.publisher_state, Page.PUBLISHER_STATE_PENDING)
        
        # master approves and publishes the page
        # first approve slave-home
        slave_page = self.reload(self.slave_page)
        publish_page(slave_page, self.user_master)
        page = self.reload(page)
        page = publish_page(page, self.user_master)
        
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
            
            page = self.reload(page)

            # login as super user and approve/publish the page
            page = publish_page(page, self.user_super)

            # there should now be 0 plugins
            self.assertEquals(CMSPlugin.objects.all().count(), 0)

    def test_superuser_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        with self.login_user_context(self.user_super):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_staff_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        all_view_perms = PagePermission.objects.filter(can_view=True)
        # verifiy that the user_staff has access to this page
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b:
                if perm.user == self.user_staff:
                    has_perm = True
        self.assertEqual(has_perm, False)
        login_ok = self.client.login(username=self.user_staff.username, password=self.user_staff.username)
        self.assertTrue(login_ok)
        # really logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        login_user_id = self.client.session.get('_auth_user_id')
        user = User.objects.get(username=self.user_staff.username)
        self.assertEquals(login_user_id,user.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_user_normal_can_view(self):
        url = self.page_b.get_absolute_url(language='en')
        all_view_perms = PagePermission.objects.filter(can_view=True)
        # verifiy that the normal_user has access to this page
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b:
                if perm.user == self.user_normal:
                    has_perm = True
        self.assertEqual(has_perm, True)
        with self.login_user_context(self.user_normal):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        
        # verifiy that the user_non_global has not access to this page
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b:
                if perm.user == self.user_non_global:
                    has_perm = True
        with self.login_user_context(self.user_non_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
        # non logged in user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_globalpermission(self):
        # Global user
        user_global = User(username="global", is_active=True)
        user_global.set_password("global")
        user_global.save()
        with self.login_user_context(self.user_super):
            user_global = create_page_user(user_global, user_global)
            user_global.is_staff = False
            user_global.save() # Prevent is_staff permission
            global_page = create_page("global", "nav_playground.html", "en",
                                      published=True)
            # Removed call since global page user doesn't have publish permission
            #global_page = publish_page(global_page, user_global)
            # it's allowed for the normal user to view the page
            assign_user_to_page(global_page, user_global, 
                                global_permission=True, can_view=True)
        
        url = global_page.get_absolute_url('en')
        all_view_perms = PagePermission.objects.filter(can_view=True)
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b and perm.user == user_global:
                has_perm = True
        self.assertEqual(has_perm, False)
        
        global_page_perm_q = Q(user=user_global) & Q(can_view=True)
        global_view_perms = GlobalPagePermission.objects.filter(global_page_perm_q).exists()
        self.assertEqual(global_view_perms, True)
        
        # user_global
        with self.login_user_context(user_global):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        # self.non_user_global
        has_perm = False
        for perm in all_view_perms:
            if perm.page == self.page_b and perm.user == self.user_non_global:
                has_perm = True
        self.assertEqual(has_perm, False)

        global_page_perm_q = Q(user=self.user_non_global) & Q(can_view=True)
        global_view_perms = GlobalPagePermission.objects.filter(global_page_perm_q).exists()
        self.assertEqual(global_view_perms, False)
        
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
    }
    
    def setUp(self):
        # create super user
        self.user_super = User(username="super", is_staff=True, is_active=True, 
            is_superuser=True)
        self.user_super.set_password("super")
        self.user_super.save()
        with self.login_user_context(self.user_super):
        
            self.home_page = create_page("home", "nav_playground.html", "en",
                                         created_by=self.user_super)
            
            # master page & master user
            
            self.master_page = create_page("master", "nav_playground.html", "en")
    
            # create master user
            self.user_master = User.objects.create(username="master", email="master@django-cms.org", password="master", is_staff=True)
            self.user_master.user_permissions.add(Permission.objects.get(codename='publish_page'))
            #self.user_master = create_page_user(self.user_super, master, grant_all=True)
            
            # assign master user under home page
            assign_user_to_page(self.home_page, self.user_master,
                                grant_on=ACCESS_DESCENDANTS, grant_all=True)
            
            # and to master page
            assign_user_to_page(self.master_page, self.user_master, grant_all=True)
            
            # slave page & slave user
            
            self.slave_page = create_page("slave-home", "nav_playground.html", "en",
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
                can_move_page=True)
            
            # publish after creating all drafts
            publish_page(self.home_page, self.user_super)
            publish_page(self.master_page, self.user_super)

        with self.login_user_context(self.user_slave):
        
            # all of them are under moderation... 
            self.pa = create_page("pa", "nav_playground.html", "en", parent=self.slave_page)
            self.pb = create_page("pb", "nav_playground.html", "en", parent=self.pa, position="right")
            self.pc = create_page("pc", "nav_playground.html", "en", parent=self.pb, position="right")
            
            self.pd = create_page("pd", "nav_playground.html", "en", parent=self.pb)
            self.pe = create_page("pe", "nav_playground.html", "en", parent=self.pd, position="right")
            
            self.pf = create_page("pf", "nav_playground.html", "en", parent=self.pe)
            self.pg = create_page("pg", "nav_playground.html", "en", parent=self.pf, position="right")
            self.ph = create_page("ph", "nav_playground.html", "en", parent=self.pf, position="right")
            
            self.assertFalse(self.pg.publisher_public)
            
            # login as master for approval
            publish_page(self.slave_page, self.user_master)
            
            # publish and approve them all
            publish_page(self.pa, self.user_master)
            publish_page(self.pb, self.user_master)
            publish_page(self.pc, self.user_master)
            publish_page(self.pd, self.user_master)
            publish_page(self.pe, self.user_master)
            publish_page(self.pf, self.user_master)
            publish_page(self.pg, self.user_master)
            publish_page(self.ph, self.user_master)

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

        2. perform move operations:
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
        self.assertEqual(self.pg.parent_id, self.pe.pk)
        # perform moves under slave...
        self.move_page(self.pg, self.pc)
        # Draft page is now under PC
        self.assertEqual(self.pg.parent_id, self.pc.pk)
        # Public page is still under PE
        self.assertEqual(self.pg.publisher_public.parent_id, self.pe.publisher_public_id)

        # We have to reload pe when using mptt >= 0.4.2, 
        # so that mptt realized that pg is no longer a child of pe
        #self.pe = self.pe.reload()
        self.move_page(self.pe, self.pg)
        self.assertEqual(self.pe.parent_id, self.pg.pk)
        self.assertEqual(self.pe.publisher_public.parent_id, self.pb.publisher_public_id)

        # check urls - they should stay them same, there wasn't approved yet
        self.assertEqual(
            self.pg.publisher_public.get_absolute_url(), 
            u'%smaster/slave-home/pb/pe/pg/' % self.get_pages_root()
        )
        self.assertEqual(
            self.ph.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pb/pe/ph/' % self.get_pages_root()
        )

        # login as master, and approve moves
        publish_page(self.pg, self.user_master)
        publish_page(self.pe, self.user_master)
        self.ph = self.ph.reload()
        # TODO: this should not be necessary
        publish_page(self.ph, self.user_master)
        publish_page(self.pf, self.user_master)
        
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
        with force_language("en"):
            pages_root = urllib.unquote(reverse("pages-root"))
        page1 = create_page('page', 'nav_playground.html', 'en', published=True)
        call_command('cms', 'moderator', 'on')
        with force_language("en"):
            path = page1.get_absolute_url()[len(pages_root):].strip('/')
            page2 = get_page_from_path(path)
        self.assertEqual(page1.get_absolute_url(), page2.get_absolute_url())
        
    def test_switch_moderator_off(self):
        with force_language("en"):
            pages_root = urllib.unquote(reverse("pages-root"))
            page1 = create_page('page', 'nav_playground.html', 'en', published=True)
            path = page1.get_absolute_url()[len(pages_root):].strip('/')
            page2 = get_page_from_path(path)
            self.assertEqual(page1.get_absolute_url(), page2.get_absolute_url())


class PermissionTestsBase(SettingsOverrideTestCase):

    settings_overrides = {
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


class ViewPermissionTests(PermissionTestsBase):
    
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


class PagePermissionTests(PermissionTestsBase):

    PermissionTestsBase.settings_overrides['CMS_CACHE_DURATIONS'] = {
        'permissions': 360
        }

    def test_page_permission_cache_invalidation(self):
        """user belongs to group which is given page_permission over page.
        Test the fact that if page_permission changes then
        page is rendered with with respect to the new page_permisison.
        This is to assert that the permissions cache is properly
        invalidated.
        """
        user = User(username='user', email='user@domain.com', password='user',
                    is_staff=True)
        user.save()
        group = Group.objects.create(name='testgroup')
        group.user_set.add(user)
        page = create_page('A', 'nav_playground.html', 'en')
        page_permission = PagePermission.objects.create(
            can_change_permissions=True, group=group, page=page)
        request = self.get_request(user)
        self.assertTrue(page.has_change_permissions_permission(request))
        page_permission.can_change_permissions = False
        page_permission.save()
        request = self.get_request(user)
        # re-fetch the page from the db to so that the page doesn't have
        # the permission_user_cache attribute set
        page = Page.objects.get(pk=page.pk)
        self.assertFalse(page.has_change_permissions_permission(request))
        
        
