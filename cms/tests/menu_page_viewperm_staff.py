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
    
    def test_public_pages_anonymous_norestrictions(self):
        """
        All pages are INVISIBLE to an anonymous user
        """
        all_pages = self._setup_tree_pages()
        granted = []
        self.assertGrantedVisibility(all_pages, granted)
    
    def test_public_menu_anonymous_user(self):
        """
        Anonymous sees nothing, as he is no staff
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = []
        self.assertGrantedVisibility(all_pages, granted)

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
        self.assertGrantedVisibility(all_pages, granted, username='user_1')
        # user 1 is member of group_b_access_page_and_children
        client = Client()
        login_ok = client.login(username='user_1', password='user_1')
        self.assertTrue(login_ok)
        self.assertTrue('_auth_user_id' in client.session)
        login_user_id = client.session.get('_auth_user_id')
        user = User.objects.get(username='user_1')
        self.assertEquals(login_user_id, user.id)
        url = self.get_pages_root()
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context['request'].user.is_authenticated(), True)
        self.assertEquals(response.context['request'].user.is_staff, True)
        # call /
        url = "/en/page_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_c/"
        self.assertPageFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageFound(url, client)
        
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
        self.assertGrantedVisibility(all_pages, granted, username='user_1_nostaff')
        client = Client()
        login_ok = client.login(username='user_1_nostaff', password='user_1_nostaff')
        self.assertTrue(login_ok)
        self.assertTrue('_auth_user_id' in client.session)
        login_user_id = client.session.get('_auth_user_id')
        user = User.objects.get(username='user_1_nostaff')
        self.assertEquals(login_user_id, user.id)
        # login worked
        url = '/en/page_b/'
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context['request'].user.is_authenticated(), True)
        self.assertEquals(response.context['request'].user.is_staff, False)
        url = "/en/page_b/page_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageFound(url, client)
        url = "/en/page_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageNotFound(url, client)
   
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
        self.assertGrantedVisibility(all_pages, granted, username='user_2')
        client = Client()
        login_ok = client.login(username='user_2', password='user_2')
        self.assertTrue(login_ok)
        self.assertTrue('_auth_user_id' in client.session)
        login_user_id = client.session.get('_auth_user_id')
        user = User.objects.get(username='user_2')
        self.assertEquals(login_user_id, user.id)
        url = '/en/page_c/'
        response = client.get(url)
        self.assertEquals(response.context['request'].user.is_authenticated(), True)
        self.assertEquals(response.context['request'].user.is_staff, True)
        self.assertEqual(response.status_code, 200)
        
        url = '/en/page_b/'
        self.assertPageNotFound(url, client)
        url = '/en/page_b/page_b_b/'
        self.assertPageNotFound(url, client)
        url = '/en/page_b/page_b_b/page_b_b_a/'
        self.assertPageFound(url, client)
        url = '/en/page_b/page_b_b/page_b_b_b/'
        self.assertPageFound(url, client)
        url = '/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/'
        self.assertPageNotFound(url, client)
        url = '/en/page_d/'
        self.assertPageNotFound(url, client)
        url = '/en/page_d/page_d_a/'
        self.assertPageFound(url, client)
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
        self.assertGrantedVisibility(all_pages, granted, username='user_2_nostaff')
        client = Client()
        login_ok = client.login(username='user_2_nostaff', password='user_2_nostaff')
        self.assertTrue(login_ok)
        # member of group that has access to this page
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageNotFound(url, client)
        
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
        self.assertGrantedVisibility(all_pages, granted, username='user_3')
        client = Client()
        login_ok = client.login(username='user_3', password='user_3')
        self.assertEqual(login_ok , True)
        url = self.get_pages_root()
        self.assertPageFound(url, client)
        url = "/en/page_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self.assertPageFound(url, client)
        url = "/en/page_c/"
        self.assertPageFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_b/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_c/"
        self.assertPageFound(url, client)
        
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
        self.assertGrantedVisibility(all_pages, granted, username='user_3_nostaff')
        client = Client()
        login_ok = client.login(username='user_3_nostaff', password='user_3_nostaff')
        self.assertTrue(login_ok)
        # call /
        url = self.get_pages_root()
        response = client.get(url)
        self.assertEqual(response.status_code, 404)
        url = "/en/page_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self.assertPageFound(url, client)
        url = "/en/page_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_c/"
        self.assertPageNotFound(url, client)
        
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
        self.assertGrantedVisibility(all_pages, granted, username='user_4')
        client = Client()
        login_ok = client.login(username='user_4', password='user_4')
        self.assertTrue(login_ok)
        # call /
        url = self.get_pages_root()
        self.assertPageFound(url, client)
        url = "/en/page_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageNotFound(url, client)
        # not a direct child
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self.assertPageFound(url, client)
        url = "/en/page_c/"
        self.assertPageFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_b/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_c/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_d/"
        self.assertPageFound(url, client)
         
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
        self.assertGrantedVisibility(all_pages, granted, username='user_4_nostaff')
        client = Client()
        login_ok = client.login(username='user_4_nostaff', password='user_4_nostaff')
        self.assertTrue(login_ok)
        url = self.get_pages_root()
        self.assertPageNotFound(url, client)
        url = "/en/page_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self.assertPageFound(url, client)
        url = "/en/page_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_d/"
        self.assertPageNotFound(url, client) 

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
        self.assertGrantedVisibility(all_pages, granted, username='user_5')
        client = Client()
        login_ok = client.login(username='user_5', password='user_5')
        self.assertTrue(login_ok)
        url = self.get_pages_root()
        self.assertPageFound(url, client)
        url = "/en/page_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_c/"
        self.assertPageFound(url, client)
        url = "/en/page_d/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageFound(url, client)
        
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
        self.assertGrantedVisibility(all_pages, granted, username='user_5_nostaff')
        client = Client()
        login_ok = client.login(username='user_5_nostaff', password='user_5_nostaff')
        self.assertTrue(login_ok)
        url = self.get_pages_root()
        self.assertPageNotFound(url, client)
        url = "/en/page_d/"
        self.assertPageFound(url, client)
        url = "/en/page_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_d/"
        self.assertPageNotFound(url, client)
        url = "/en/page_b/page_b_b/page_b_b_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/"
        self.assertPageFound(url, client)
        url = "/en/page_d/page_d_a/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_b/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_c/"
        self.assertPageNotFound(url, client)
        url = "/en/page_d/page_d_d/"
        self.assertPageNotFound(url, client)

