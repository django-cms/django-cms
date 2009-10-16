from django.contrib.auth.models import User
from django.conf import settings
from cms.tests.base import CMSTestCase, URL_CMS_PAGE_ADD, URL_CMS_PAGE,\
    URL_CMS_PAGE_CHANGE
from cms.models import Title, Page



class PermissionModeratorTestCase(CMSTestCase):
    """Permissions and moderator together
    
    Fixtures contains 3 users and 1 published page and some other stuff
    
    Users:
        1. `super`: superuser
        2. `master`: user with permissions to all applications
        3. `slave`: user assigned to page `slave-home` can add/change/delete page
    
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
                    - assigned slave user which can add/change/delete this page and its descendants
                    - `master` user want to moderate this page and all descendants
                    
        4. `pageA`:
            - created by super
            - master can add/change/delete on it and descendants 
    """
    
    #./manage.sh dumpdata  -e south -e contenttypes -e reversion > ../cms/tests/fixtures/permission.json
    fixtures = ['../cms/tests/fixtures/permission.json']
    
    
    def setUp(self):
        self.user_super = User.objects.get(username="super")
        self.user_master = User.objects.get(username="master")
        self.user_slave = User.objects.get(username="slave")
    
    
    # helpers
    
    def _add_plugin(self, user):
        slave_page = self.slave_page
        
        post_data = {
            'language': 'en',
            'page_id': slave_page.pk,
            'placeholder': 'Right-Column',
            'plugin_type': 'TextPlugin'
        }
        self.login_user(user)
        url = URL_CMS_PAGE + "%d/add-plugin/" % slave_page.pk
        response = self.client.post(url, post_data)
        self.assertEqual(response.content, "1")
        
    
    
    def _publish_page(self, page, approve=False, user=None, published_check=True):
        if user:
            self.login_user(user)
            
        # publish / approve page by master
        response = self.client.post(URL_CMS_PAGE + "%d/change-status/" % page.pk, {1 :1})
        self.assertEqual(response.status_code, 200)
        
        if not approve:
            return self.reload_page(page)
        
        # approve
        page = self._approve_page(page)
        
        if published_check:
            # must have public object now
            assert(page.publisher_public)
            # and public object must be published
            assert(page.publisher_public.published)
        
        return page
    
    def _approve_page(self, page):
        response = self.client.get(URL_CMS_PAGE + "%d/approve/" % page.pk)
        self.assertRedirects(response, URL_CMS_PAGE)
        # reload page
        return self.reload_page(page)
    
    def _check_published_page_attributes(self, page):
        public_page = page.publisher_public
        
        if page.parent:
            self.assertEqual(page.parent_id, public_page.parent.publisher_draft.id)
        
        self.assertEqual(page.level, public_page.level)
        
        # TODO: add check for siblings
        
        draft_siblings = list(page.get_siblings(True). \
            filter(publisher_is_draft=True).order_by('tree_id', 'parent', 'lft'))
        public_siblings = list(public_page.get_siblings(True). \
            filter(publisher_is_draft=False).order_by('tree_id', 'parent', 'lft'))
        
        skip = 0
        for i, sibling in enumerate(draft_siblings):
            if not sibling.publisher_public_id:
                skip += 1
                continue
            self.assertEqual(sibling.id, public_siblings[i - skip].publisher_draft.id) 
    
    
    @property
    def home_page(self):
        return Page.objects.drafts().get(title_set__slug="home")
    
    @property
    def slave_page(self):
        return Page.objects.drafts().get(title_set__slug="slave-home")
    
    @property
    def master_page(self):
        return Page.objects.drafts().get(title_set__slug="master")
    
    
    # tests
            
    def test_00_test_configuration(self):
        """Just check if we have right configuration for this test. Problem lies
        in cms_settings!! something like cms_settings.CMS_MODERATOR = True just
        doesn't work!!!
        
        TODO: settings must be changed to be configurable / overridable
        """
        assert(settings.CMS_PERMISSION)
        assert(settings.CMS_MODERATOR)
    
    
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
        slave_page = self.slave_page
        page_data = self.get_new_page_data()
        
        # reuest moderation
        page_data.update({
            #'moderator_state': Page.MODERATOR_NEED_APPROVEMENT,
            #'moderator_message': "Approve me!",
            '_save': 'Save',
        })
        
        # add page
        url = URL_CMS_PAGE_ADD + "?target=%d&position=first-child" % slave_page.pk
        response = self.client.post(url, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        # public model shouldn't be available yet, because of the moderation
        self.assertObjectExist(Title.objects, slug=page_data['slug'])
        self.assertObjectDoesNotExist(Title.objects.public(), slug=page_data['slug'])
        
        # page created?
        page = self.assertObjectExist(Page.objects.drafts(), title_set__slug=page_data['slug'])
        # moderators and approvemnt right?
        self.assertEqual(page.get_moderator_queryset().count(), 1)
        #assert(page.moderator_state == Page.MODERATOR_NEED_APPROVEMENT)
        
        # must not have public object yet
        assert(not page.publisher_public)
        
        # publish / approve page by master
        self.login_user(self.user_master)
        
        response = self.client.post(URL_CMS_PAGE + "%d/change-status/" % page.pk, {1 :1})
        self.assertEqual(response.status_code, 200)
        
        # approve / publish
        page = self._approve_page(page)
        
    
    def test_06_super_can_add_plugin(self):
        self._add_plugin(self.user_super)
    
    
    def test_07_master_can_add_plugin(self):
        self._add_plugin(self.user_master)
    
        
    def test_08_slave_can_add_plugin(self):
        self._add_plugin(self.user_slave)
    
    def test_09_same_order(self):
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
            page = self._publish_page(page, True)
            self._check_published_page_attributes(page)
    
    
    def test_10_create_copy_publish(self):
        # create new page to copy
        self.login_user(self.user_master)
        page = self.create_page(self.slave_page)
        
        # copy it under home page...
        copied_page = self.copy_page(page, self.home_page)
        
        page = self._publish_page(copied_page, True)
        self._check_published_page_attributes(page)
    
    
    def test_11_create_publish_copy(self):
        # create new page to copy
        self.login_user(self.user_master)
        page = self.create_page(self.home_page)
        
        page = self._publish_page(page, True)
        
        # copy it under master page...
        copied_page = self.copy_page(page, self.master_page)
        
        self._check_published_page_attributes(page)
        self._check_published_page_attributes(copied_page)
        
        
    def test_12_subtree_needs_approvement(self):
        self.login_user(self.user_master)
        # create page under slave_page
        page = self.create_page(self.home_page)
        assert(not page.publisher_public)
        
        # create subpage uner page
        subpage = self.create_page(page)
        assert(not subpage.publisher_public)
        
        # publish both of them in reverse order 
        subpage = self._publish_page(subpage, True, published_check=False) 
        
        # subpage should not be published, because parent is not published 
        # yet, should be marked as `publish when parent`
        assert(not subpage.publisher_public) 
        
        # pagemoderator state must be set
        self.assertEqual(subpage.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish page (parent of subage), so subpage must be published also
        page = self._publish_page(page, True)
        assert(page.publisher_public)
        
        # reload subpage, it was probably changed
        subpage = self.reload_page(subpage)
        
        # parent was published, so subpage must be also published..
        assert(subpage.publisher_public) 
        
        #check attributes
        self._check_published_page_attributes(page)
        self._check_published_page_attributes(subpage)


    def test_13_subtree_with_super(self):
        self.login_user(self.user_super)
        # create page under root
        page = self.create_page()
        assert(not page.publisher_public)
        
        # create subpage under page
        subpage = self.create_page(page)
        assert(not subpage.publisher_public)
        
        # tree id must be the same
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        # publish both of them  
        page = self._publish_page(page, True)
        # reload subpage, there were an tree_id change
        subpage = self.reload_page(subpage)
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        subpage = self._publish_page(subpage, True)
        # tree id must stay the same
        self.assertEqual(page.tree_id, subpage.tree_id)
        
        # published pages must also have the same tree_id
        self.assertEqual(page.publisher_public.tree_id, subpage.publisher_public.tree_id)
        
        #check attributes
        self._check_published_page_attributes(page) 
        self._check_published_page_attributes(subpage)
        
    def test_14_super_add_page_to_root(self):
        """Create page which is not under moderation in root, and check if 
        some properties are correct.
        """
        self.login_user(self.user_super)
        # create page under root
        page = self.create_page()
        
        # public must not exist
        assert(not page.publisher_public)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
    
    def test_15_moderator_flags(self):
        """Add page under slave_home and check its flag
        """
        self.login_user(self.user_slave)
        page = self.create_page(self.slave_page)
        
        # moderator_state must be changed
        self.assertEqual(page.moderator_state, Page.MODERATOR_CHANGED)
        
        # check publish box
        page = self._publish_page(page, published_check=False)
        
        # page should request approvement now
        self.assertEqual(page.moderator_state, Page.MODERATOR_NEED_APPROVEMENT)
        
        # approve it by master
        self.login_user(self.user_master)

        # approve this page - but it doesn't get published yet, because 
        # slave home is not published
        page = self._approve_page(page)
        
        # public page must not exist because of parent
        assert(not page.publisher_public)
        
        # waiting for parents
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        
        # publish slave page
        slave_page = self._publish_page(self.slave_page)
        
        assert(not page.publisher_public)
        assert(not slave_page.publisher_public)
        
        # they must be approved first
        slave_page = self._approve_page(slave_page)
        
        # master is approved
        self.assertEqual(slave_page.moderator_state, Page.MODERATOR_APPROVED)
        
        # reload page
        page = self.reload_page(page)
        
        # page must be approved also now
        self.assertEqual(page.moderator_state, Page.MODERATOR_APPROVED)
        
        
    def test_16_patricks_move(self):
        """Special name, special case..

        1. build following tree (msater node is approved and published)
        
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
        
        
        assert(not pg.publisher_public)
        
        # login as master for approvement
        self.login_user(self.user_master)
        
        # first approve slave-home
        self._publish_page(self.slave_page, approve=True)
        
        # publish and approve them all
        pa = self._publish_page(pa, approve=True)
        pb = self._publish_page(pb, approve=True)
        pc = self._publish_page(pc, approve=True)
        pd = self._publish_page(pd, approve=True)
        pe = self._publish_page(pe, approve=True)
        pf = self._publish_page(pf, approve=True)
        pg = self._publish_page(pg, approve=True)
        ph = self._publish_page(ph, approve=True)
        
        # parent check
        self.assertEqual(pe.parent, pb)
        self.assertEqual(pg.parent, pe)
        self.assertEqual(ph.parent, pe)
        
        # not published yet, cant exist
        assert(pg.publisher_public)
        
        # check urls
        self.assertEqual(pg.publisher_public.get_absolute_url(), u'/master/slave-home/pb/pe/pg/')
        self.assertEqual(ph.publisher_public.get_absolute_url(), u'/master/slave-home/pb/pe/ph/')
        
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
        
        
        # check urls - they should stay them same, there wasn't approvement yet
        self.assertEqual(pg.publisher_public.get_absolute_url(), u'/master/slave-home/pb/pe/pg/')
        self.assertEqual(ph.publisher_public.get_absolute_url(), u'/master/slave-home/pb/pe/ph/')
        
        # pg & pe should require approvement
        self.assertEqual(pg.requires_approvement(), True)
        self.assertEqual(pe.requires_approvement(), True)
        self.assertEqual(ph.requires_approvement(), False)
        
        # login as master, and approve moves
        self.login_user(self.user_master)
        pg = self._approve_page(pg)
        pe = self._approve_page(pe)
        ph = self._approve_page(ph)
        pf = self._approve_page(pf)
        
        # public parent check after move
        self.assertEqual(pg.publisher_public.parent.pk, pc.publisher_public_id)
        self.assertEqual(pe.publisher_public.parent.pk, pg.publisher_public_id)
        self.assertEqual(ph.publisher_public.parent.pk, pe.publisher_public_id)
        
        # check if urls are correct after move
        self.assertEqual(pg.publisher_public.get_absolute_url(), u'/master/slave-home/pc/pg/')
        self.assertEqual(ph.publisher_public.get_absolute_url(), u'/master/slave-home/pc/pg/pe/ph/')        
        
        
        