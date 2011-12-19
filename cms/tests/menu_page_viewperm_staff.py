# -*- coding: utf-8 -*-
from __future__ import with_statement

from cms.tests.menu_page_viewperm import ViewPermissionTests
from cms.models import Page

from django.contrib.sites.models import Site
from django.contrib.auth.models import  User
from django.test.client import Client
        

class ViewPermissionComplexMenuStaffNodeTests(ViewPermissionTests):
    """
    Test CMS_PUBLIC_FOR=staff group access and menu nodes rendering
    """
    settings_overrides = {
        'CMS_MODERATOR': False,
        'CMS_PERMISSION': True,
        'CMS_PUBLIC_FOR': 'staff',
    }
    def setUp(self):
        super(ViewPermissionComplexMenuStaffNodeTests, self).setUp()
        self.site = Site()
        self.site.pk = 1
        self.client = Client()
    
    def tearDown(self):
        self.client.logout()
        super(ViewPermissionComplexMenuStaffNodeTests, self).tearDown()    
  
    def test_public_pages_anonymous_norestrictions(self):
        """
        All pages are INVISIBLE to an anonymous user
        """
        all_pages = self._setup_tree_pages()
        granted = []
        self._check_grant_visiblity(all_pages, granted)
    
    def test_public_menu_anonymous_user(self):
        """
        Anonymous sees nothing, as he is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = []
        self._check_grant_visiblity(all_pages, granted)

    def test_node_staff_access_page_and_children_group_1(self):
        """
        simulate behaviour of group b member
        group_b_ACCESS_PAGE_AND_CHILDREN to page_b
        staff user
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_b',
                   'page_b_a',
                   'page_b_b',
                   'page_b_c',
                   'page_b_d',
                   'page_c',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_1')
        # user 1 is member of group_b_access_page_and_children
        login_ok = self.client.login(username='user_1', password='user_1')
        self.assertTrue(login_ok , True)
        self.assertTrue('_auth_user_id' in self.client.session)
        login_user_id = self.client.session.get('_auth_user_id')
        user = User.objects.get(username='user_1')
        self.assertEquals(login_user_id, user.id)
        url = self.get_pages_root()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context['request'].user.is_authenticated(), True)
        self.assertEquals(response.context['request'].user.is_staff, True)
        # call /
        url = "/en/page_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_c/"
        self._check_url_page_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        
    def test_node_staff_access_page_and_children_group_1_no_staff(self):
        """
        simulate behaviour of group b member
        group_b_ACCESS_PAGE_AND_CHILDREN to page_b
        no staff user
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [ 
                   'page_b',
                   'page_b_a',
                   'page_b_b',
                   'page_b_c',
                   'page_b_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_1_nostaff')
        login_ok = self.client.login(username='user_1_nostaff', password='user_1_nostaff')
        self.assertTrue(login_ok , True)
        self.assertTrue('_auth_user_id' in self.client.session)
        login_user_id = self.client.session.get('_auth_user_id')
        user = User.objects.get(username='user_1_nostaff')
        self.assertEquals(login_user_id, user.id)
        # login worked
        url = '/en/page_b/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context['request'].user.is_authenticated(), True)
        self.assertEquals(response.context['request'].user.is_staff, False)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_found(url)
        url = "/en/page_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_not_found(url)
   
    def test_node_staff_access_children_group_2(self):
        """
        simulate behaviour of group 2 member
        GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
        to page_b_b and user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
                   'page_b_b_a',
                   'page_b_b_b',
                   'page_b_b_c',
                   'page_c',
                   'page_d_a',
                   'page_d_b',
                   'page_d_c',
                   'page_d_d',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_2')
        login_ok = self.client.login(username='user_2', password='user_2')
        self.assertEqual(login_ok , True)
        self.assertTrue('_auth_user_id' in self.client.session)
        login_user_id = self.client.session.get('_auth_user_id')
        user = User.objects.get(username='user_2')
        self.assertEquals(login_user_id, user.id)
        url = '/en/page_c/'
        response = self.client.get(url)
        self.assertEquals(response.context['request'].user.is_authenticated(), True)
        self.assertEquals(response.context['request'].user.is_staff, True)
        self.assertEqual(response.status_code, 200)
        
        url = '/en/page_b/'
        self._check_url_page_not_found(url)
        url = '/en/page_b/page_b_b/'
        self._check_url_page_not_found(url)
        url = '/en/page_b/page_b_b/page_b_b_a/'
        self._check_url_page_found(url)
        url = '/en/page_b/page_b_b/page_b_b_b/'
        self._check_url_page_found(url)
        url = '/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/'
        self._check_url_page_not_found(url)
        url = '/en/page_d/'
        self._check_url_page_not_found(url)
        url = '/en/page_d/page_d_a/'
        self._check_url_page_found(url)
        
#        
    def test_node_staff_access_children_group_2_nostaff(self):
        """
        simulate behaviour of group 2 member
        GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
        to page_b_b and user is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_b_b_a',
                   'page_b_b_b',
                   'page_b_b_c',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_2_nostaff')
        login_ok = self.client.login(username='user_2_nostaff', password='user_2_nostaff')
        self.assertEqual(login_ok , True)
        # member of group that has access to this page
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_not_found(url)
        
    def test_node_staff_access_page_and_descendants_group_3(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS to page_b
        and user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
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
        url = self.get_pages_root()
        self._check_url_page_found(url)
        url = "/en/page_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_found(url)
        url = "/en/page_c/"
        self._check_url_page_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_b/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_c/"
        self._check_url_page_found(url)
        
    def test_node_staff_access_page_and_descendants_group_3_nostaff(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS to page_b
        user is not staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_b',
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
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_3_nostaff')
        login_ok = self.client.login(username='user_3_nostaff', password='user_3_nostaff')
        self.assertEqual(login_ok , True)
        # call /
        url = self.get_pages_root()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        url = "/en/page_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_found(url)
        url = "/en/page_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_c/"
        self._check_url_page_not_found(url)
        
    def test_node_staff_access_descendants_group_4(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS to page_b_b
        user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
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
        # call /
        url = self.get_pages_root()
        self._check_url_page_found(url)
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_not_found(url)
        # not a direct child
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_found(url)
        url = "/en/page_c/"
        self._check_url_page_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_b/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_c/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_d/"
        self._check_url_page_found(url)
         
    def test_node_staff_access_descendants_group_4_nostaff(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS to page_b_b
        user is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = [
                   'page_b_b_a',
                   'page_b_b_a_a',
                   'page_b_b_b',
                   'page_b_b_c',
        ]
        self._check_grant_visiblity(all_pages, granted, username='user_4_nostaff')
        login_ok = self.client.login(username='user_4_nostaff', password='user_4_nostaff')
        self.assertEqual(login_ok , True)
        url = self.get_pages_root()
        self._check_url_page_not_found(url)
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_found(url)
        url = "/en/page_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_d/"
        self._check_url_page_not_found(url) 

    def test_node_staff_access_page_group_5(self):
        """
        simulate behaviour of group b member
        group_d_ACCESS_PAGE to page_d
        user is staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
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
        url = self.get_pages_root()
        self._check_url_page_found(url)
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_c/"
        self._check_url_page_found(url)
        url = "/en/page_d/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        
        
    def test_node_staff_access_page_group_5_nostaff(self):
        """
        simulate behaviour of group b member
        group_d_ACCESS_PAGE to page_d
        nostaff user
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_d',]
        self._check_grant_visiblity(all_pages, granted, username='user_5_nostaff')
        login_ok = self.client.login(username='user_5_nostaff', password='user_5_nostaff')
        self.assertEqual(login_ok , True)
        url = self.get_pages_root()
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_found(url)
        url = "/en/page_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_d/"
        self._check_url_page_not_found(url)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_a/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_b/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_c/"
        self._check_url_page_not_found(url)
        url = "/en/page_d/page_d_d/"
        self._check_url_page_not_found(url)

