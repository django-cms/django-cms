# -*- coding: utf-8 -*-
from cms.models import Page, CMSPlugin
from cms.models.moderatormodels import ACCESS_DESCENDANTS
from cms.test.testcases import CMSTestCase, URL_CMS_PAGE_ADD, URL_CMS_PLUGIN_REMOVE
from cms.utils.permissions import has_generic_permission
from django.conf import settings
from django.contrib.auth.models import User

class PermissionModeratorTestCase(CMSTestCase):
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
    def setUp(self):
        # create super user
        self.user_super = User(username="super", is_staff=True, is_active=True, 
            is_superuser=True)
        self.user_super.set_password("super")
        self.user_super.save()
        self.login_user(self.user_super)
        
        self.home_page = self.create_page(title="home", user=self.user_super)
        
        # master page & master user
        
        self.master_page = self.create_page(title="master")

        # create master user
        self.user_master = self.create_page_user("master", grant_all=True)
        
        # assign master user under home page
        self.assign_user_to_page(self.home_page, self.user_master, grant_on=ACCESS_DESCENDANTS,
            grant_all=True)
        
        # and to master page
        self.assign_user_to_page(self.master_page, self.user_master, grant_all=True)
        
        # slave page & slave user
        
        self.slave_page = self.create_page(title="slave-home", parent_page=self.master_page, user=self.user_super)  
        self.user_slave = self.create_page_user("slave", 
            can_add_page=True, can_change_page=True, can_delete_page=True)
        
        self.assign_user_to_page(self.slave_page, self.user_slave, grant_all=True)
        
        # create page_a - sample page from master
        
        page_a = self.create_page(title="pageA", user=self.user_super)
        self.assign_user_to_page(page_a, self.user_master, 
            can_add=True, can_change=True, can_delete=True, can_publish=True, 
            can_move_page=True, can_moderate=True)
        
        # publish after creating all drafts
        self.publish_page(self.home_page)
        self.publish_page(self.master_page)
        # logg in as master, and request moderation for slave page and descendants
        self.request_moderation(self.slave_page, 7)
        
        self.client.logout()
    
    def test_00_test_configuration(self):
        """Just check if we have right configuration for this test. Problem lies
        in cms_settings!! something like cms_settings.CMS_MODERATOR = True just
        doesn't work!!!
        
        TODO: settings must be changed to be configurable / overridable
        """
        self.assertEqual(settings.CMS_PERMISSION, True)
        self.assertEqual(settings.CMS_MODERATOR, True)
    
    def test_01_super_can_add_page_to_root(self, status_code=200):
        self.login_user(self.user_super)
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
    
    def test_02_master_can_add_page_to_root(self, status_code=403):
        self.login_user(self.user_master)
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
        
    def test_03_slave_can_add_page_to_root(self, status_code=403):
        self.login_user(self.user_slave)
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
    
    def test_04_moderation_on_slave_home(self):
        self.assertEqual(self.slave_page.get_moderator_queryset().count(), 1)
    
    def test_05_slave_can_add_page_under_slave_home(self):
        self.login_user(self.user_slave)
        
        # move to admin.py?
        # url = URL_CMS_PAGE_ADD + "?target=%d&position=last-child" % slave_page.pk
        
        # can he even access it over get?
        # response = self.client.get(url)
        # self.assertEqual(response.status_code, 200)
        
        # add page
        page = self.create_page(self.slave_page, user=self.user_slave)
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
        self.publish_page(page, False, self.user_slave, False)
        
        # user_slave is moderator for this page
        # approve / publish as user_slave
        # user master should be able to approve aswell
        page = self.approve_page(page)

    def test_06_page_added_by_slave_can_be_published_approved_by_user_master(self):
        self.login_user(self.user_master)
        
        # add page
        page = self.create_page(self.slave_page, user=self.user_slave)
        # same as test_05_slave_can_add_page_under_slave_home        
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        self.assertTrue(page.moderator_state == Page.MODERATOR_CHANGED)
        
        # must not have public object yet
        self.assertFalse(page.publisher_public)
                
        # print ('descendants of master page (%s): ' % self.master_page.pk) + str([(spage, spage.pk) for spage in self.reload_page(self.master_page).get_descendants()])
        
        # print ('ancestors of created page (%s): ' % page.pk) +  str([(spage, spage.pk) for spage in page.get_ancestors()])
        
        # print ('descendants of slave page (%s): ' % self.slave_page.pk) + str([(spage, spage.pk) for spage in self.reload_page(self.slave_page).get_descendants()])
        
        # print ('ancestors of slave page (%s): ' % self.slave_page.pk)  +  str([(spage, spage.pk) for spage in self.slave_page.get_ancestors()])

        self.assertTrue(has_generic_permission(page.pk, self.user_master, "publish", 1))
        # should be True user_master should have publish permissions for childred aswell
        # don't test for published since publishing must be approved
        self.publish_page(page, False, self.user_master, False)
        
        # user_master is moderator for top level page / but can't approve descendants?
        # approve / publish as user_master
        # user master should be able to approve descendants
        page = self.approve_page(page)    
        
    def test_07_super_can_add_plugin(self):
        self.add_plugin(self.user_super, page=self.slave_page)
    
    
    def test_08_master_can_add_plugin(self):
        self.add_plugin(self.user_master, page=self.slave_page)
    
    
    def test_09_slave_can_add_plugin(self):
        self.add_plugin(self.user_slave, page=self.slave_page)
    
    
    def test_10_same_order(self):
        self.login_user(self.user_master)
        
        # create 4 pages
        slugs = []
        for i in range(0, 4):
            page = self.create_page(self.home_page)
            slug = page.title_set.drafts()[0].slug
            slugs.append(slug)
        
        # approve last 2 pages in reverse order
        for slug in reversed(slugs[2:]):
            page = self.assertObjectExist(Page.objects.drafts(), title_set__slug=slug)
            page = self.publish_page(page, True)
            self.check_published_page_attributes(page)
    
    def test_11_create_copy_publish(self):
        # create new page to copy
        self.login_user(self.user_master)
        page = self.create_page(self.slave_page)
        
        # copy it under home page...
        copied_page = self.copy_page(page, self.home_page)
        
        page = self.publish_page(copied_page, True)
        self.check_published_page_attributes(page)
    
    
    def test_12_create_publish_copy(self):
        # create new page to copy
        self.login_user(self.user_master)
        page = self.create_page(self.home_page)
        
        page = self.publish_page(page, True)
        
        # copy it under master page...
        copied_page = self.copy_page(page, self.master_page)
        
        self.check_published_page_attributes(page)
        copied_page = self.publish_page(copied_page, True)
        self.check_published_page_attributes(copied_page)
        
        
    def test_13_subtree_needs_approvement(self):
        self.login_user(self.user_master)
        # create page under slave_page
        page = self.create_page(self.home_page)
        self.assertEqual(not page.publisher_public, True)
        
        # create subpage uner page
        subpage = self.create_page(page)
        self.assertEqual(not subpage.publisher_public, True)
        
        # publish both of them in reverse order 
        subpage = self.publish_page(subpage, True, published_check=False) 
        
        # subpage should not be published, because parent is not published 
        # yet, should be marked as `publish when parent`
        self.assertEqual(not subpage.publisher_public, True) 
        
        # pagemoderator state must be set
        self.assertEqual(subpage.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish page (parent of subage), so subpage must be published also
        page = self.publish_page(page, True)
        self.assertEqual(page.publisher_public != None, True)
        
        # reload subpage, it was probably changed
        subpage = self.reload_page(subpage)
        
        # parent was published, so subpage must be also published..
        self.assertEqual(subpage.publisher_public != None, True) 
        
        #check attributes
        self.check_published_page_attributes(page)
        self.check_published_page_attributes(subpage)


    def test_14_subtree_with_super(self):
        self.login_user(self.user_super)
        # create page under root
        page = self.create_page()
        self.assertEqual(not page.publisher_public, True)
        
        # create subpage under page
        subpage = self.create_page(page)
        self.assertEqual(not subpage.publisher_public, True)
        
        # tree id must be the same
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        # publish both of them  
        page = self.publish_page(page, True)
        # reload subpage, there were an tree_id change
        subpage = self.reload_page(subpage)
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        subpage = self.publish_page(subpage, True)
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
        self.login_user(self.user_super)
        # create page under root
        page = self.create_page()
        
        # public must not exist
        self.assertFalse(page.publisher_public)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
    
    
    def test_16_moderator_flags(self):
        """Add page under slave_home and check its flag
        """
        self.login_user(self.user_slave)
        page = self.create_page(parent_page=self.slave_page)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
        
        # check publish box
        page = self.publish_page(page, published_check=False)
        
        # page should request approvement now
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # approve it by master
        self.login_user(self.user_master)

        # approve this page - but it doesn't get published yet, because 
        # slave home is not published
        page = self.approve_page(page)
        
        # public page must not exist because of parent
        self.assertEqual(not page.publisher_public, True)
        
        # waiting for parents
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish slave page
        slave_page = self.publish_page(self.slave_page, published_check=False)
        
        self.assertEqual(not page.publisher_public, True)
        self.assertEqual(not slave_page.publisher_public, True)
        
        # they must be approved first
        slave_page = self.approve_page(slave_page)
        
        # master is approved
        self.assertEqual(slave_page.moderator_state, Page.MODERATOR_APPROVED)
        
        # reload page
        page = self.reload_page(page)
        
        # page must be approved also now
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)
        
        
    def test_17_patricks_move(self):
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
        self.login_user(self.user_slave)
        
        # all of them are under moderation... 
        pa = self.create_page(self.slave_page, title="pa")
        pb = self.create_page(pa, position="right", title="pb")
        pc = self.create_page(pb, position="right", title="pc")
        
        pd = self.create_page(pb, title="pd")
        pe = self.create_page(pd, position="right", title="pe")
        
        pf = self.create_page(pe, title="pf")
        pg = self.create_page(pf, position="right", title="pg")
        ph = self.create_page(pf, position="right", title="ph")
        
        self.assertEqual(not pg.publisher_public, True)
        
        # login as master for approval
        self.login_user(self.user_master)
        
        # first approve slave-home
        self.publish_page(self.slave_page, approve=True)
        
        # publish and approve them all
        pa = self.publish_page(pa, approve=True)
        pb = self.publish_page(pb, approve=True)
        pc = self.publish_page(pc, approve=True)
        pd = self.publish_page(pd, approve=True)
        pe = self.publish_page(pe, approve=True)
        pf = self.publish_page(pf, approve=True)
        pg = self.publish_page(pg, approve=True)
        ph = self.publish_page(ph, approve=True)
        
        # parent check
        self.assertEqual(pe.parent, pb)
        self.assertEqual(pg.parent, pe)
        self.assertEqual(ph.parent, pe)
        
        # not published yet, cant exist
        self.assertEqual(pg.publisher_public != None, True)
        
        # check urls
        self.assertEqual(pg.publisher_public.get_absolute_url(), u'%smaster/slave-home/pb/pe/pg/' % self.get_pages_root())
        self.assertEqual(ph.publisher_public.get_absolute_url(), u'%smaster/slave-home/pb/pe/ph/' % self.get_pages_root())
        
        # perform movings under slave...
        self.login_user(self.user_slave)
        pg = self.move_page(pg, pc)
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
        self.assertEqual(pg.publisher_public.get_absolute_url(), u'%smaster/slave-home/pb/pe/pg/' % self.get_pages_root())
        self.assertEqual(ph.publisher_public.get_absolute_url(), u'%smaster/slave-home/pb/pe/ph/' % self.get_pages_root())
        
        # pg & pe should require approval
        self.assertEqual(pg.requires_approvement(), True)
        self.assertEqual(pe.requires_approvement(), True)
        self.assertEqual(ph.requires_approvement(), False)
        
        # login as master, and approve moves
        self.login_user(self.user_master)
        pg = self.approve_page(pg)
        pe = self.approve_page(pe)
        ph = self.approve_page(ph)
        pf = self.approve_page(pf)
        
        # public parent check after move
        self.assertEqual(pg.publisher_public.parent.pk, pc.publisher_public_id)
        self.assertEqual(pe.publisher_public.parent.pk, pg.publisher_public_id)
        self.assertEqual(ph.publisher_public.parent.pk, pe.publisher_public_id)
        
        # check if urls are correct after move
        self.assertEqual(pg.publisher_public.get_absolute_url(), u'%smaster/slave-home/pc/pg/' % self.get_pages_root())
        self.assertEqual(ph.publisher_public.get_absolute_url(), u'%smaster/slave-home/pc/pg/pe/ph/' % self.get_pages_root())     
        
    def test_18_plugins_get_published(self):
        self.login_user(self.user_super)
        # create page under root
        page = self.create_page()
        self.add_plugin(self.user_super, page)
        # public must not exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        self.publish_page(page, True, self.user_super, True)
        self.assertEqual(CMSPlugin.objects.all().count(), 2)

    def test_19_remove_plugin_page_under_moderation(self):
        # login as slave and create page
        self.login_user(self.user_slave)
        page = self.create_page(self.slave_page)
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        
        # add plugin
        plugin_id = self.add_plugin(self.user_slave, page)
        
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)

        # publish page
        page = self.publish_page(page, published_check=False)
        
        # only the draft plugin should exist
        self.assertEqual(CMSPlugin.objects.all().count(), 1)
        
        # page should require approval
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # master approves and publishes the page
        self.login_user(self.user_master)
        # first approve slave-home
        self.publish_page(self.slave_page, approve=True)
        page = self.publish_page(page, approve=True)
        
        # draft and public plugins should now exist
        self.assertEqual(CMSPlugin.objects.all().count(), 2)
        
        # login as slave and delete the plugin - should require moderation
        self.login_user(self.user_slave)
        plugin_data = {
            'plugin_id': plugin_id
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
        self.login_user(self.user_super)
        page = self.publish_page(page, approve=True)
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)

        # there should now be 0 plugins
        self.assertEquals(CMSPlugin.objects.all().count(), 0)
