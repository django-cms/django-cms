# -*- coding: utf-8 -*-
from __future__ import with_statement

from cms.api import create_page
from cms.menu import CMSMenu, get_visible_pages
from cms.models import Page
from cms.models import ACCESS_DESCENDANTS, ACCESS_CHILDREN, ACCESS_PAGE
from cms.models import ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE_AND_DESCENDANTS 
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.test_utils.testcases import SettingsOverrideTestCase


from django.contrib.sites.models import Site
from django.contrib.auth.models import AnonymousUser, User, Permission, Group
from django.db.models import Q
from django.test.client import Client
from cms.models.titlemodels import Title


class ViewPermissionTests(SettingsOverrideTestCase):
    """
    Test various combinations of view permissions pages and menus
    Focus on the different grant types and inheritance options of grant on
    Given the tree:
        
        |- Page_a
        |- Page_b
        | |- Page_b_a
        | |- Page_b_b
        | | |- Page_b_b_a
        | | | |- Page_b_b_a_a
        | | |- Page_b_b_b
        | | |- Page_b_b_c
        | |- Page_b_c
        | |- Page_b_d
        | | |- Page_b_d_a
        | | |- Page_b_d_b
        | | |- Page_b_d_c
        |- Page_c
        |- Page_d
        | |- Page_d_a
        | |- Page_d_b
        | |- Page_d_c
    """
    GROUPNAME_1 = 'group_b_ACCESS_PAGE_AND_CHILDREN'
    GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
    GROUPNAME_3 = 'group_b_ACCESS_PAGE_AND_DESCENDANTS'
    GROUPNAME_4 = 'group_b_b_ACCESS_DESCENDANTS'
    GROUPNAME_5 = 'group_d_ACCESS_PAGE'
    
    def _setup_tree_pages(self):
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        page_a = create_page("page_a", **stdkwargs) # first page slug is /
        page_b = create_page("page_b", **stdkwargs)
        page_c = create_page("page_c", **stdkwargs)
        page_d = create_page("page_d", **stdkwargs)
        
        page_b_a = create_page("page_b_a", parent=page_b, **stdkwargs)
        page_b_b = create_page("page_b_b", parent=page_b, **stdkwargs)
        page_b_b_a = create_page("page_b_b_a", parent=page_b_b, **stdkwargs)
        page_b_b_b = create_page("page_b_b_b", parent=page_b_b, **stdkwargs)
        page_b_b_c = create_page("page_b_b_c", parent=page_b_b, **stdkwargs)
        page_b_b_a_a = create_page("page_b_b_a_a", parent=page_b_b_a, **stdkwargs)
        
        page_b_c = create_page("page_b_c", parent=page_b, **stdkwargs)
        page_b_d = create_page("page_b_d", parent=page_b, **stdkwargs)
        page_b_d_a = create_page("page_b_d_a", parent=page_b_d, **stdkwargs)
        page_b_d_b = create_page("page_b_d_b", parent=page_b_d, **stdkwargs)
        page_b_d_c = create_page("page_b_d_c", parent=page_b_d, **stdkwargs)
        
        page_d_a = create_page("page_d_a", parent=page_d, **stdkwargs)
        page_d_b = create_page("page_d_b", parent=page_d, **stdkwargs)
        page_d_c = create_page("page_d_c", parent=page_d, **stdkwargs) 
        page_d_d = create_page("page_d_d", parent=page_d, **stdkwargs)
        
        return [page_a,
                page_b,
                page_b_a,
                page_b_b,
                page_b_b_a,
                page_b_b_a_a,
                page_b_b_b,
                page_b_b_c,
                page_b_c,
                page_b_d,
                page_b_d_a,
                page_b_d_b,
                page_b_d_c,
                page_c,
                page_d,
                page_d_a,
                page_d_b,
                page_d_c,
                page_d_d,
    ]
        
    def _setup_user_groups(self):
        """
        Setup a group for every grant on ACCESS TYPE
        """
        user = User.objects.create(username='user_1', email='user_1@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_1)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_1_nostaff', email='user_1_nostaff@domain.com', is_active=True, is_staff=False)
        user.set_password(user.username)
        user.save()
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_2', email='user_2@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_2)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_2_nostaff', email='user_2_nostaff@domain.com', is_active=True, is_staff=False)
        user.set_password(user.username)
        user.save()
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_3', email='user_3@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_3)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_3_nostaff', email='user_3_nostaff@domain.com', is_active=True, is_staff=False)
        user.set_password(user.username)
        user.save()
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_4', email='user_4@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_4)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_4_nostaff', email='user_4_nostaff@domain.com', is_active=True, is_staff=False)
        user.set_password(user.username)
        user.save()
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_5', email='user_5@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_5)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_5_nostaff', email='user_5_nostaff@domain.com', is_active=True, is_staff=False)
        user.set_password(user.username)
        user.save()
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_staff', email='user_staff@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        
        self.assertEquals(11, User.objects.all().count())
        
        
    def _setup_view_restrictions(self):
        """
        Setup a view restriction with every type of the grant_on ACCESS_*
        'group_b_ACCESS_PAGE_AND_CHILDREN' 
        'group_b_b_ACCESS_CHILDREN'
        'group_b_ACCESS_PAGE_AND_DESCENDANTS'
        'group_b_b_ACCESS_DESCENDANTS'
        'group_d_ACCESS_PAGE'
        """
        
        page = Page.objects.get(title_set__title="page_b")
        group = Group.objects.get(name__iexact=self.GROUPNAME_1)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE_AND_CHILDREN)
        
        page = Page.objects.get(title_set__title="page_b_b")
        group = Group.objects.get(name__iexact=self.GROUPNAME_2)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_CHILDREN)
        
        page = Page.objects.get(title_set__title="page_b")
        group = Group.objects.get(name__iexact=self.GROUPNAME_3)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        
        page = Page.objects.get(title_set__title="page_b_b")
        group = Group.objects.get(name__iexact=self.GROUPNAME_4)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_DESCENDANTS)
        
        page = Page.objects.get(title_set__title="page_d")
        group = Group.objects.get(name__iexact=self.GROUPNAME_5)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE)
        
        self.assertEquals(5, PagePermission.objects.all().count())
        self.assertEquals(0, GlobalPagePermission.objects.all().count())
        
        
    def _check_url_page_found(self, url):
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
    
    def _check_url_page_not_found(self, url):
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)
        
    def _check_is_view_restricted_check(self, check_page):
        """
        Manually check the single page if there is any restriction applied
        code taken from 2.1.3 permissionmerge2
        """
        anchestor_ids = check_page.get_ancestors().values_list('id', flat=True)
        q = (Q(page__tree_id=check_page.tree_id) & (Q(page__id__in=anchestor_ids) | Q(page__id=check_page.id)) & (
            Q(page=check_page) 
            | (Q(page__level__lt=check_page.level) & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS)))
            | (Q(page__level=check_page.level - 1) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN)))
            )
        )
        return PagePermission.objects.filter(q).order_by('page__level').filter(can_view=True).exists()
    
    def _check_db_view_restriction_to_page(self, page_title, expected_result):
        page_to_check = Page.objects.get(title_set__title=page_title)
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, expected_result)
        
    def _check_node_memberships(self, visible_page_ids, restricted_pages, public_page_ids):
        for page_id in visible_page_ids:
            in_restricted = False
            in_public = False
            if page_id in restricted_pages: 
                in_restricted = True
            if page_id in public_page_ids:
                in_public = True
            self.assertTrue((in_public and not in_restricted) or
                             (not in_public and in_restricted),
                              msg="page_id %s in_public: %s, in_restricted: %s" % (page_id, in_public, in_restricted))
                              
    def _check_grant_visiblity(self, all_pages, expected_granted_pages, username=None):
        """
        helper function to check the expected_granted_pages are 
        not in the restricted_pages list and 
        all visible pages are in the expected_granted_pages
        """
        # log the user in if present
        user = None
        if username is not None:
            user = User.objects.get(username__iexact=username)
        request = self.get_request(user)
        visible_page_ids = get_visible_pages(request, all_pages, self.site)
    	self.assertTrue(len(visible_page_ids) == len(expected_granted_pages))
        public_page_ids = Page.objects.filter(title_set__title__in=expected_granted_pages).values_list('id', flat=True)
        restricted_pages = Page.objects.exclude(title_set__title__in=expected_granted_pages).values_list('id', flat=True)
        self._check_node_memberships(visible_page_ids, restricted_pages, public_page_ids)
        
    def get_request(self, user=None):
        attrs = {
            'user': user or AnonymousUser(),
            'REQUEST': {},
            'session': {},
        }
        return type('Request', (object,), attrs)


class ViewPermissionComplexMenuAllNodesTests(ViewPermissionTests):
    """
    Test CMS_PUBLIC_FOR=all group access and menu nodes rendering
    """
    settings_overrides = {
        'CMS_MODERATOR': False,
        'CMS_PERMISSION': True,
        'CMS_PUBLIC_FOR': 'all',
    }
    def setUp(self):
        super(ViewPermissionComplexMenuAllNodesTests, self).setUp()
        self.site = Site()
        self.site.pk = 1
       
    def tearDown(self):
        super(ViewPermissionComplexMenuAllNodesTests, self).tearDown()    
    
    def test_public_pages_anonymous_norestrictions(self):
        """
        All pages are visible to an anonymous user
        """
        all_pages = self._setup_tree_pages()
        request = self.get_request()
        visible_page_ids = get_visible_pages(request, all_pages, self.site)
        is_same = (len(all_pages) == len(visible_page_ids))
        self.assertTrue(is_same)
        
    def test_public_menu_anonymous_user(self):
        """
        Anonymous user should only see the pages in the rendered menu
        that have no permissions assigned,directly or indirectly
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a', 
                   'page_c', 
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d'
        ]
        self._check_grant_visiblity( all_pages, granted)
 
    def test_menu_access_page_and_children_group_1(self):
        """
        simulate behaviour of group b member
        group_b_ACCESS_PAGE_AND_CHILDREN to page_b
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_c',
                   #group_1
                   'page_b', #page_id b has page_id and children restricted - group 1
                   'page_b_a',
                   'page_b_b', #page_id b_b children restricted - group 2
                   'page_b_c',
                   'page_b_d',
                   # not restricted
                   'page_d_a', 
                   'page_d_b', 
                   'page_d_c', 
                   'page_d_d'
        ]
        self._check_grant_visiblity(all_pages, granted,username='user_1')
        login_ok = self.client.login(username='user_1', password='user_1')
        self.assertEqual(login_ok , True)
        url = "/en/page_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_found(url)
        # descendant
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        # group 5
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        # should be public as only page_d is restricted
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        
    def test_menu_access_children_group_2(self):
        """
        simulate behaviour of group 2 member
        GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
        to page_b_b
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [
                 'page_a',
                 'page_c',
                 'page_b_b_a',
                 'page_b_b_b',
                 'page_b_b_c',
                 # not restricted
                 'page_d_a',
                 'page_d_b',
                 'page_d_c',
                 'page_d_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_2')
        login_ok = self.client.login(username='user_2', password='user_2')
        self.assertEqual(login_ok , True)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        
    def test_menu_access_page_and_descendants_group_3(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS to page_b
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [ 'page_a',
                    'page_b',
                    'page_b_a',
                    'page_b_b',
                    'page_b_b_a',
                    'page_b_b_a_a',
                    'page_b_b_b',
                    'page_b_b_c',
                    'page_b_c',
                    'page_b_d',
                    'page_b_d_a',
                    'page_b_d_b',
                    'page_b_d_c',
                    'page_c',
                    'page_d_a',
                    'page_d_b',
                    'page_d_c',
                    'page_d_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_3')
        login_ok = self.client.login(username='user_3', password='user_3')
        self.assertEqual(login_ok , True)
        url = "/en/page_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_d/page_b_d_a/"
        self._check_url_page_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        
    def test_menu_access_descendants_group_4(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS to page_b_b
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [ 'page_a',
                   'page_b_b_a',
                   'page_b_b_a_a',
                   'page_b_b_b',
                   'page_b_b_c',
                   'page_c',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_4')
        login_ok = self.client.login(username='user_4', password='user_4')
        self.assertEqual(login_ok , True)
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        
    def test_menu_access_page_group_5(self):
        """
        simulate behaviour of group b member
        group_d_ACCESS_PAGE to page_d
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [ 'page_a',
                    'page_c',
                    'page_d',
                    'page_d_a',
                    'page_d_b',
                    'page_d_c',
                    'page_d_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_5')
        login_ok = self.client.login(username='user_5', password='user_5')
        self.assertEqual(login_ok , True)
        # call /
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        



class ViewPermissionTreeBugTests(ViewPermissionTests):
    """Test issue 1113
    https://github.com/divio/django-cms/issues/1113
    Wrong view permission calculation in PagePermission.objects.for_page
    Assign only: grant_on=ACCESS_PAGE to page
    Test if this affects the menu entries
    """
    settings_overrides = {
        'CMS_MODERATOR': False,
        'CMS_PERMISSION': True,
        'CMS_PUBLIC_FOR': 'all',
    }
    GROUPNAME_6 = 'group_6_ACCESS_PAGE'  
    
    def setUp(self):
        super(ViewPermissionTreeBugTests, self).setUp()
        self.site = Site()
        self.site.pk = 1
       
    def tearDown(self):
        super(ViewPermissionTreeBugTests, self).tearDown()
        self.site = None
        
    def _setup_pages(self):
        """
        Tree Structure
            |- Page_1
            |  |- Page_2
            |    |- Page_3
            |      |- Page_4 (false positive)
            |  |- Page_5
            |  |  |- Page_6 (group 6 page access)
        """
        stdkwargs = {
            'template': 'nav_playground.html',
            'language': 'en',
            'published': True,
            'in_navigation': True,
        }
        page_1 = create_page("page_1", **stdkwargs) # first page slug is /
        page_2 = create_page("page_2", parent=page_1, **stdkwargs)
        page_3 = create_page("page_3", parent=page_2, **stdkwargs)
        page_4 = create_page("page_4", parent=page_3, **stdkwargs)
        page_5 = create_page("page_5", parent=page_1, **stdkwargs)
        page_6 = create_page("page_6", parent=page_5, **stdkwargs)
        return [page_1,
                page_2,
                page_3,
                page_4,
                page_5,
                page_6,
        ]
    
    def _setup_user(self):
        user = User.objects.create(username='user_6', email='user_6@domain.com', is_active=True, is_staff=True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_6)
        group.user_set.add(user)
        group.save()
        
    def _setup_permviewbug(self):
        """
        Setup group_6_ACCESS_PAGE view restriction 
        """
        page = Page.objects.get(title_set__title="page_6")
        group = Group.objects.get(name__iexact=self.GROUPNAME_6)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE)
            
    def test_pageforbug(self):
        all_pages=self._setup_pages()
        self._setup_user()
        self._setup_permviewbug()
        for page in all_pages:
            perm = PagePermission.objects.for_page(page=page)
            # only page_6 has a permission assigned
            if page.get_title() == 'page_6':
                self.assertTrue(len(perm)==1)
            else:
                self.assertTrue(len(perm)==0)
        granted = [ 'page_1',
                    'page_2',
                    'page_3',
                    'page_4',
                    'page_5',
        ]
        # anonymous sees page_6 not
        self._check_grant_visiblity(all_pages, granted)
        url = "/en/page_2/page_3/page_4/"
        self._check_url_page_found(url)
        url = "/en/page_5/"
        self._check_url_page_found(url)
        url = "/en/page_5/page_6/"
        self._check_url_page_not_found(url)
        # group member
        granted = [ 'page_1',
                    'page_2',
                    'page_3',
                    'page_4',
                    'page_5',
                    'page_6',
        ]
        self._check_grant_visiblity(all_pages, granted,username='user_6')
        login_ok = self.client.login(username='user_6', password='user_6')
        self.assertEqual(login_ok , True)
        url = "/en/page_2/page_3/page_4/"
        self._check_url_page_found(url)
        url = "/en/page_5/page_6/"
        self._check_url_page_found(url)
        
        