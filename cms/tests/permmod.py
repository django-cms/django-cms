# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page, publish_page, approve_page, add_plugin
from cms.models import Page, CMSPlugin
from cms.test_utils.testcases import (URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_REMOVE, 
    SettingsOverrideTestCase, URL_CMS_PLUGIN_ADD)
from cms.utils.permissions import has_generic_permission
from django.contrib.auth.models import User

class PermissionModeratorTestCase(SettingsOverrideTestCase):
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
    fixtures = ['permmod.json']
    settings_overrides = {
        'CMS_PERMISSION': True,
        'CMS_MODERATOR': True,
    }
    
    pages = {
        'home': 1,
        'master': 2,
        'slave': 3,
    }
    
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

    def test_01_super_can_add_page_to_root(self, status_code=200):
        self.login_user(User.objects.get(username='super'))
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
    
    def test_02_master_can_add_page_to_root(self, status_code=403):
        self.login_user(User.objects.get(username='master'))
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
        
    def test_03_slave_can_add_page_to_root(self, status_code=403):
        self.login_user(User.objects.get(username='slave'))
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
    
    def test_04_moderation_on_slave_home(self):
        slave_page = Page.objects.get(pk=self.pages['slave'])
        self.assertEqual(slave_page.get_moderator_queryset().count(), 1)
    
    def test_05_slave_can_add_page_under_slave_home(self):
        user_slave = User.objects.get(username='slave')
        self.login_user(user_slave)
        slave_page = Page.objects.get(pk=self.pages['slave'])
        
        # move to admin.py?
        # url = URL_CMS_PAGE_ADD + "?target=%d&position=last-child" % slave_page.pk
        
        # can he even access it over get?
        # response = self.client.get(url)
        # self.assertEqual(response.status_code, 200)
        
        # add page
        page = create_page("page", "nav_playground.html", "en",
                           parent=slave_page, created_by=user_slave)
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

        self.assertTrue(has_generic_permission(page.pk, user_slave, "publish", 1))

        # publish as slave, published as user_master before 
        publish_page(page, user_slave)
        
        # user_slave is moderator for this page
        # approve / publish as user_slave
        # user master should be able to approve aswell
        page = approve_page(page, user_slave)

    def test_06_page_added_by_slave_can_be_published_approved_by_user_master(self):
        user_master = User.objects.get(username='master')
        user_slave = User.objects.get(username='slave')
        slave_page = Page.objects.get(pk=self.pages['slave'])
        
        # add page
        page = create_page("page", "nav_playground.html", "en",
                           parent=slave_page, created_by=user_slave)
        # same as test_05_slave_can_add_page_under_slave_home        
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        self.assertTrue(page.moderator_state == Page.MODERATOR_CHANGED)
        
        # must not have public object yet
        self.assertFalse(page.publisher_public)
                
        self.assertTrue(has_generic_permission(page.pk, user_master, "publish", 1))
        # should be True user_master should have publish permissions for childred aswell
        # don't test for published since publishing must be approved
        publish_page(page, user_master)
        
        # user_master is moderator for top level page / but can't approve descendants?
        # approve / publish as user_master
        # user master should be able to approve descendants
        page = approve_page(page, user_master)    
        
    def test_07_super_can_add_plugin(self):
        user_super = User.objects.get(username='super')
        slave_page = Page.objects.get(pk=self.pages['slave'])
        self._add_plugin(user_super, page=slave_page)
    
    def test_08_master_can_add_plugin(self):
        user_master = User.objects.get(username='master')
        slave_page = Page.objects.get(pk=self.pages['slave'])
        self._add_plugin(user_master, page=slave_page)
    
    def test_09_slave_can_add_plugin(self):
        user_slave = User.objects.get(username='slave')
        slave_page = Page.objects.get(pk=self.pages['slave'])
        self._add_plugin(user_slave, page=slave_page)
    
    def test_10_same_order(self):
        user_master = User.objects.get(username='master')
        home_page = Page.objects.get(pk=self.pages['home'])
        
        # create 4 pages
        slugs = []
        for i in range(0, 4):
            page = create_page("page", "nav_playground.html", "en",
                               parent=home_page)
            slug = page.title_set.drafts()[0].slug
            slugs.append(slug)
        
        # approve last 2 pages in reverse order
        for slug in reversed(slugs[2:]):
            page = self.assertObjectExist(Page.objects.drafts(), title_set__slug=slug)
            page = publish_page(page, user_master, True)
            self.check_published_page_attributes(page)
    
    def test_11_create_copy_publish(self):
        user_master = User.objects.get(username='master')
        home_page = Page.objects.get(pk=self.pages['home'])
        slave_page = Page.objects.get(pk=self.pages['slave'])
        # create new page to copy
        page = create_page("page", "nav_playground.html", "en",
                           parent=slave_page)
        
        # copy it under home page...
        # TODO: Use page.copy_page here
        with self.login_user_context(user_master):
            copied_page = self.copy_page(page, home_page)
        
        page = publish_page(copied_page, user_master, True)
        self.check_published_page_attributes(page)
    
    
    def test_12_create_publish_copy(self):
        user_master = User.objects.get(username='master')
        home_page = Page.objects.get(pk=self.pages['home'])
        master_page = Page.objects.get(pk=self.pages['master'])
        # create new page to copy
        page = create_page("page", "nav_playground.html", "en",
                           parent=home_page)
        
        page = publish_page(page, user_master, True)
        
        # copy it under master page...
        # TODO: Use page.copy_page here
        with self.login_user_context(user_master):
            copied_page = self.copy_page(page, master_page)
        
        self.check_published_page_attributes(page)
        copied_page = publish_page(copied_page, user_master, True)
        self.check_published_page_attributes(copied_page)
        
        
    def test_13_subtree_needs_approvement(self):
        user_master = User.objects.get(username='master')
        home_page = Page.objects.get(pk=self.pages['home'])
        # create page under slave_page
        page = create_page("parent", "nav_playground.html", "en",
                           parent=home_page)
        self.assertFalse(page.publisher_public)
        
        # create subpage uner page
        subpage = create_page("subpage", "nav_playground.html", "en", parent=page)
        self.assertFalse(subpage.publisher_public)
        
        # publish both of them in reverse order 
        subpage = publish_page(subpage, user_master, True) 
        
        # subpage should not be published, because parent is not published 
        # yet, should be marked as `publish when parent`
        self.assertFalse(subpage.publisher_public) 
        
        # pagemoderator state must be set
        self.assertEqual(subpage.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish page (parent of subage), so subpage must be published also
        page = publish_page(page, user_master, True)
        self.assertNotEqual(page.publisher_public, None)
        
        # reload subpage, it was probably changed
        subpage = self.reload_page(subpage)
        
        # parent was published, so subpage must be also published..
        self.assertNotEqual(subpage.publisher_public, None) 
        
        #check attributes
        self.check_published_page_attributes(page)
        self.check_published_page_attributes(subpage)


    def test_14_subtree_with_super(self):
        user_super = User.objects.get(username='super')
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
        page = publish_page(page, user_super, True)
        # reload subpage, there were an tree_id change
        subpage = self.reload_page(subpage)
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        subpage = publish_page(subpage, user_super, True)
        # tree id must stay the same
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        # published pages must also have the same tree_id
        self.assertEqual(page.publisher_public.tree_id, subpage.publisher_public.tree_id)
        
        #check attributes
        self.check_published_page_attributes(page) 
        self.check_published_page_attributes(subpage)
        
        
    def test_15_super_add_page_to_root(self):
        """Create page which is not under moderation in root, and check if 
        some properties are correct.
        """
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        
        # public must not exist
        self.assertFalse(page.publisher_public)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
    
    
    def test_16_moderator_flags(self):
        """Add page under slave_home and check its flag
        """
        user_slave = User.objects.get(username='slave')
        slave_page = Page.objects.get(pk=self.pages['slave'])
        user_master = User.objects.get(username='master')
        page = create_page("page", "nav_playground.html", "en",
                           parent=slave_page)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
        
        # check publish box
        page = publish_page(page, user_slave)
        
        # page should request approvement now
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # approve it by master

        # approve this page - but it doesn't get published yet, because 
        # slave home is not published
        page = approve_page(page, user_master)
        
        # public page must not exist because of parent
        self.assertFalse(page.publisher_public)
        
        # waiting for parents
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish slave page
        slave_page = publish_page(slave_page, user_master)
        
        self.assertFalse(page.publisher_public)
        self.assertFalse(slave_page.publisher_public)
        
        # they must be approved first
        slave_page = approve_page(slave_page, user_master)
        
        # master is approved
        self.assertEqual(slave_page.moderator_state, Page.MODERATOR_APPROVED)
        
        # reload page
        page = self.reload_page(page)
        
        # page must be approved also now
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)
        
    def test_17_plugins_get_published(self):
        user_super = User.objects.get(username='super')
        # create page under root
        page = create_page("page", "nav_playground.html", "en")
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", "en", body="test")
        # public must not exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        publish_page(page, user_super, True)
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

    def test_18_remove_plugin_page_under_moderation(self):
        # login as slave and create page
        user_slave = User.objects.get(username='slave')
        user_master = User.objects.get(username='master')
        user_super = User.objects.get(username='super')
        slave_page = Page.objects.get(pk=self.pages['slave'])
        page = create_page("page", "nav_playground.html", "en", parent=slave_page)
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        
        # add plugin
        placeholder = page.placeholders.all()[0]
        plugin = add_plugin(placeholder, "TextPlugin", "en", body="test")
        
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)

        # publish page
        page = self.reload(page)
        page = publish_page(page, user_slave)
        
        # only the draft plugin should exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        
        # page should require approval
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # master approves and publishes the page
        # first approve slave-home
        slave_page = self.reload(slave_page)
        publish_page(slave_page, user_master, approve=True)
        page = self.reload(page)
        page = publish_page(page, user_master, approve=True)
        
        # draft and public plugins should now exist
        self.assertEqual(CMSPlugin.objects.all().count(), 2)
        
        # login as slave and delete the plugin - should require moderation
        self.login_user(user_slave)
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
        page = publish_page(page, user_super, approve=True)
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)

        # there should now be 0 plugins
        self.assertEquals(CMSPlugin.objects.all().count(), 0)

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
    fixtures = ['patrick.json']
    settings_overrides = {
        'CMS_PERMISSION': True,
        'CMS_MODERATOR': True,
    }
    
    pages = {
        'home': 1,
        'master': 2,
        'slave': 3,
    }
    def test_patricks_move(self):
        """Special name, special case..

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
        pages = dict([(p.get_slug('en'), p) for p in Page.objects.drafts()])
        pa = pages['pa']
        pb = pages['pb']
        pc = pages['pc']
        pd = pages['pd']
        pe = pages['pe']
        pf = pages['pf']
        pg = pages['pg']
        ph = pages['ph']
        user_master = User.objects.get(username='master')
        pg = self.move_page(pg, pc)
        # We have to reload pe when using mptt >= 0.4.2, 
        # so that mptt realized that pg is no longer a child of pe
        pe = self.reload_page(pe)
        pe = self.move_page(pe, pg)
        
        # reload all - moving has changed some attributes
        pa = self.reload_page(pa)
        pb = self.reload_page(pb)
        pc = self.reload_page(pc)
        pd = self.reload_page(pd)
        pe = self.reload_page(pe)
        pf = self.reload_page(pf)
        pg = self.reload_page(pg)
        ph = self.reload_page(ph)
        
        # check urls - they should stay them same, there wasn't approved yet
        self.assertEqual(
            pg.publisher_public.get_absolute_url(), 
            u'%smaster/slave-home/pb/pe/pg/' % self.get_pages_root()
        )
        self.assertEqual(
            ph.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pb/pe/ph/' % self.get_pages_root()
        )
        
        # pg & pe should require approval
        self.assertEqual(pg.requires_approvement(), True)
        self.assertEqual(pe.requires_approvement(), True)
        self.assertEqual(ph.requires_approvement(), False)
        
        # login as master, and approve moves
        pg = approve_page(pg, user_master)
        pe = approve_page(pe, user_master)
        ph = approve_page(ph, user_master)
        pf = approve_page(pf, user_master)
        
        # public parent check after move
        self.assertEqual(pg.publisher_public.parent.pk, pc.publisher_public_id)
        self.assertEqual(pe.publisher_public.parent.pk, pg.publisher_public_id)
        self.assertEqual(ph.publisher_public.parent.pk, pe.publisher_public_id)
        
        # check if urls are correct after move
        self.assertEqual(
            pg.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pc/pg/' % self.get_pages_root()
        )
        self.assertEqual(
            ph.publisher_public.get_absolute_url(),
            u'%smaster/slave-home/pc/pg/pe/ph/' % self.get_pages_root()
        )     