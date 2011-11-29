# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.menu import CMSMenu, get_visible_pages
from cms.models import Page, ACCESS_CHOICES
from cms.models import ACCESS_DESCENDANTS, ACCESS_CHILDREN, ACCESS_PAGE
from cms.models import ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE_AND_DESCENDANTS 
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.test_utils.fixtures.menus import (MenusFixture, SubMenusFixture, 
    SoftrootFixture)
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import (SettingsOverride, 
    LanguageOverride)
from cms.test_utils.util.mock import AttributeObject
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db.models import Q
from django.template import Template, TemplateSyntaxError
from menus.base import NavigationNode
from menus.menu_pool import menu_pool, _build_nodes_inner_for_one_menu
from menus.utils import mark_descendants, find_selected, cut_levels


        
class ViewPermissionComplexMenuAllTests(SettingsOverrideTestCase):
    """
    Test various combinations of view permissions pages and menus
    Focus on the different grant types and inheritance options of grant on
    
    Given the tree:
        
        |- Page_a
        |- Page_b
        | |- Page_b_a
        | |- Page_b_b
        | | |- Page_b_b_a
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
    settings_overrides = {
        'CMS_MODERATOR': False,
        'CMS_PERMISSION': True,
        'CMS_PUBLIC_FOR': 'all',
        'USE_I18N': False,
        'CMS_LANGUAGES':(('en', 'English'),),
        
    }
    
    GROUPNAME_1 = 'group_b_ACCESS_PAGE_AND_CHILDREN'
    GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
    GROUPNAME_3 = 'group_b_ACCESS_PAGE_AND_DESCENDANTS'
    GROUPNAME_4 = 'group_b_ACCESS_DESCENDANTS'
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
        
        page_b_c = create_page("page_b_c", parent=page_b, **stdkwargs)
        page_b_d = create_page("page_b_d", parent=page_b, **stdkwargs)
        page_b_d_a = create_page("page_b_d_a", parent=page_b_d, **stdkwargs )
        page_b_d_b = create_page("page_b_d_b", parent=page_b_d, **stdkwargs)
        page_b_d_c = create_page("page_b_d_c", parent=page_b_d, **stdkwargs)
        
        page_d_a = create_page("page_d_a",  parent=page_d, **stdkwargs)
        page_d_b = create_page("page_d_b",  parent=page_d, **stdkwargs)
        page_d_c = create_page("page_d_c",  parent=page_d, **stdkwargs) 
        page_d_d = create_page("page_d_d",  parent=page_d, **stdkwargs)
        
        return [page_a,
                page_b,
                page_b_a,
                page_b_b,
                page_b_b_a,
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
        user = User.objects.create(username='user_1', email='user_1@domain.com', is_active = True, is_staff = True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_1)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_2', email='user_2@domain.com', is_active = True, is_staff = True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_2)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_3', email='user_3@domain.com', is_active = True, is_staff = True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_3)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_4', email='user_4@domain.com', is_active = True, is_staff = True)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_4)
        group.user_set.add(user)
        group.save()
        
        user = User.objects.create(username='user_5', email='user_5@domain.com', is_active = True, is_staff = False)
        user.set_password(user.username)
        user.save()
        group = Group.objects.create(name=self.GROUPNAME_5)
        group.user_set.add(user)
        group.save()
        
    def _setup_view_restrictions(self):
        """
        Setup a view restriction with every type of the grant_on ACCESS_*
        'group_b_ACCESS_PAGE_AND_CHILDREN' 
        'group_b_b_ACCESS_CHILDREN'
        'group_b_ACCESS_PAGE_AND_DESCENDANTS'
        'group_b_b_ACCESS_DESCENDANTS'
        'group_d_ACCESS_PAGE'
        """
        
        page = Page.objects.get(title_set__title= "page_b")
        group = Group.objects.get(name__iexact = self.GROUPNAME_1)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE_AND_CHILDREN)
        
        page = Page.objects.get(title_set__title= "page_b_b")
        group = Group.objects.get(name__iexact = self.GROUPNAME_2)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_CHILDREN)
        
        page = Page.objects.get(title_set__title= "page_b")
        group = Group.objects.get(name__iexact = self.GROUPNAME_3)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
        
        page = Page.objects.get(title_set__title= "page_b_b")
        group = Group.objects.get(name__iexact = self.GROUPNAME_4)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_DESCENDANTS)
        
        page = Page.objects.get(title_set__title= "page_d")
        group = Group.objects.get(name__iexact = self.GROUPNAME_5)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE)
        
        self.assertEquals(5,PagePermission.objects.all().count())
        self.assertEquals(0,GlobalPagePermission.objects.all().count())
        
        
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
        q = (Q(page__tree_id=check_page.tree_id) & (Q(page__id__in = anchestor_ids) | Q(page__id = check_page.id)) & (
            Q(page=check_page) 
            | (Q(page__level__lt=check_page.level) & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS)))
            | (Q(page__level=check_page.level - 1) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN)))
            )
        )
        
        return PagePermission.objects.filter(q).order_by('page__level').filter(can_view=True).exists()
        
#
# TESTS START
#                
    def test_public_pages_anonymous_norestrictions(self):
        """
        All pages are rendered as menuitems to an anonymous user
        """
        all_pages=self._setup_tree_pages()
        response = self.client.get(self.get_pages_root())
        self.assertContains( response, "href=\"/en/\"" )
        self.assertContains( response, "href=\"/en/page_b/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_a/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_b/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_b/page_b_b_a/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_b/page_b_b_b/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_b/page_b_b_c/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_c/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_d/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_d/page_b_d_a/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_d/page_b_d_b/\"" )
        self.assertContains( response, "href=\"/en/page_b/page_b_d/page_b_d_c/\"" )
        self.assertContains( response, "href=\"/en/page_c/\"" )
        self.assertContains( response, "href=\"/en/page_d/\"" )
        self.assertContains( response, "href=\"/en/page_d/page_d_a/\"" )
        self.assertContains( response, "href=\"/en/page_d/page_d_b/\"" )
        self.assertContains( response, "href=\"/en/page_d/page_d_c/\"" )
        self.assertContains( response, "href=\"/en/page_d/page_d_d/\"" )
        
        
    
    def test_grant_types_menu_anonymous_user(self):
        """
        Anonymous user should only see the pages in the rendered menu
        that have no permissions assigned,directly or indirectly
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        response = self.client.get(self.get_pages_root())
        self.assertContains( response, "href=\"/en/\"" )
        #page b has page and children restricted - group 1
        self.assertNotContains( response, "href=\"/en/page_b/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_a/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_b/\"" )
        #page b_b children restricted - group 2
        #page b_b page and descendants restricted - group 3
        #page b_b descendants restricted - group 4
        self.assertNotContains( response, "href=\"/en/page_b/page_b_b/page_b_b_a/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_b/page_b_b_b/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_b/page_b_b_c/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_c/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_d/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_d/page_b_d_a/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_d/page_b_d_b/\"" )
        self.assertNotContains( response, "href=\"/en/page_b/page_b_d/page_b_d_c/\"" )
        # no restriction to page_c
        self.assertContains( response, "href=\"/en/page_c/\"" )
        #page d page restricted - group 5
        self.assertNotContains( response, "href=\"/en/page_d/\"" )
        # as the page_d is restricted and we are on a root menu level 
        # we expect the children
        # are not included too in the menu
        self.assertNotContains( response, "href=\"/en/page_d/page_d_a/\"" )
        self.assertNotContains( response, "href=\"/en/page_d/page_d_b/\"" )
        self.assertNotContains( response, "href=\"/en/page_d/page_d_c/\"" )
        self.assertNotContains( response, "href=\"/en/page_d/page_d_d/\"" )
        
    
    def test_grant_types_pages_anonymous_user(self):
        """
        Anonymous user should only see the pages in the rendered menu
        that have no permissions assigned, directly or indirectly
        but should have access to some of the not shown ones
        """
        self._setup_user_groups()
        self._setup_tree_pages()
        self._setup_view_restrictions()
        response = self.client.get(self.get_pages_root())
        self.assertContains( response, "href=\"/en/\"" )
        url ="/en/"
        self._check_url_page_found(url)
        #page b has page and children restricted - group 1
        url ="/en/page_b/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_a/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_b/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_b/page_b_b_a/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_b/page_b_b_b/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_b/page_b_b_c/"
        self._check_url_page_not_found(url)
        
        #page b_b children restricted - group 2
        #page b_b page and descendants restricted - group 3
        #page b_b descendants restricted - group 4
        
        url ="/en/page_b/page_b_c/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_d/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_d/page_b_d_a/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_d/page_b_d_b/"
        self._check_url_page_not_found(url)
        url ="/en/page_b/page_b_d/page_b_d_c/"
        self._check_url_page_not_found(url)
        
        # no restrictions
        url ="/en/page_c/"
        self._check_url_page_found(url)
        
        #page d page restricted - group 5
        url ="/en/page_d/"
        self._check_url_page_not_found(url)
        # as the page_d is restricted and 
        # but not the children
        url = "/en/page_d/page_d_a/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_b/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_c/"
        self._check_url_page_found(url)
        url = "/en/page_d/page_d_d/"
        self._check_url_page_found(url)
        
    def test_menu_access_page_and_children_group_1(self):
        """
        simulate behaviour of group b member
        group_b_ACCESS_PAGE_AND_CHILDREN
        to page_b
        
        """
        self._setup_user_groups()
        self._setup_tree_pages()
        self._setup_view_restrictions()
        self.client.logout()
        # fresh login
        # user 1 is member of group_b_access_page_and_children
        login_ok = self.client.login(username='user_1', password='user_1')
        self.assertEqual(login_ok , True)
        # call /
        url = self.get_pages_root()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url ="/en/page_b/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_a/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_b/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_c/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_d/"
        self.assertContains( response, "href=\"%s\"" % url )
        # not a direct child
        url ="/en/page_b/page_b_b/page_b_b_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b_a")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # no restrictions
        url ="/en/page_c/"
        self.assertContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_c")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, False)
        # page d is not associated with this group
        url = "/en/page_d/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        # as the page_d is restricted and 
        # but not the children
        url = "/en/page_d/page_d_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_c/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_d/"

    def test_menu_access_children_group_2(self):
        """
        simulate behaviour of group 2 member
        GROUPNAME_2 = 'group_b_b_ACCESS_CHILDREN'
        to page_b_b
        
        """
        self._setup_user_groups()
        self._setup_tree_pages()
        self._setup_view_restrictions()
        self.client.logout()
        # fresh login
        # user 1 is member of group_b_access_page_and_children
        login_ok = self.client.login(username='user_2', password='user_2')
        self.assertEqual(login_ok , True)
        # call /
        url = self.get_pages_root()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url ="/en/page_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_c/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_d/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        # not a direct child
        url ="/en/page_b/page_b_b/page_b_b_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b_a")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # no restrictions
        url ="/en/page_c/"
        self.assertContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_c")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, False)
        # page d is not associated with this group
        url = "/en/page_d/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_d")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        # as the page_d is restricted and 
        # but not the children
        url = "/en/page_d/page_d_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_c/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_d/"
        
    def test_menu_access_page_and_descendants_group_3(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS
        to page_b
        
        """
        self._setup_user_groups()
        self._setup_tree_pages()
        self._setup_view_restrictions()
        self.client.logout()
        # fresh login
        # user 1 is member of group_b_access_page_and_children
        login_ok = self.client.login(username='user_3', password='user_3')
        self.assertEqual(login_ok , True)
        # call /
        url = self.get_pages_root()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url ="/en/page_b/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_a/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_b/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_c/"
        self.assertContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_d/"
        self.assertContains( response, "href=\"%s\"" % url )
        # not a direct child
        url ="/en/page_b/page_b_b/page_b_b_a/"
        self.assertContains( response, "href=\"%s\"" % url )
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b_a")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b_b_a")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # no restrictions
        url ="/en/page_c/"
        self.assertContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_c")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, False)
        # page d is not associated with this group
        url = "/en/page_d/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_d")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # as the page_d is restricted and 
        # but not the children
        url = "/en/page_d/page_d_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_c/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_d/"
        
    def test_menu_access_descendants_group_4(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS
        to page_b_b
        
        """
        self._setup_user_groups()
        self._setup_tree_pages()
        self._setup_view_restrictions()
        self.client.logout()
        # fresh login
        # user 1 is member of group_b_access_page_and_children
        login_ok = self.client.login(username='user_4', password='user_4')
        self.assertEqual(login_ok , True)
        # call /
        url = self.get_pages_root()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url ="/en/page_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_c/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url ="/en/page_b/page_b_d/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        # not a direct child
        url ="/en/page_b/page_b_b/page_b_b_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b_a")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        # verified - the page has a view restriction
        page_to_check = Page.objects.get(title_set__title= "page_b_b_a")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # no restrictions
        url ="/en/page_c/"
        self.assertContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_c")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, False)
        # page d is not associated with this group
        url = "/en/page_d/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        page_to_check = Page.objects.get(title_set__title= "page_d")
        is_restricted = self._check_is_view_restricted_check(page_to_check)
        self.assertEquals(is_restricted, True)
        
        # as the page_d is restricted and 
        # but not the children
        url = "/en/page_d/page_d_a/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_b/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_c/"
        self.assertNotContains( response, "href=\"%s\"" % url )
        url = "/en/page_d/page_d_d/"
        
#    def test_access_togrant_access_page_and_children_group_b(self):
#        """
#        simulate behaviour of group b member
#        group_b_ACCESS_PAGE_AND_CHILDREN
#        to rendered menu
#        
#        """
#        self._setup_user_groups()
#        self._setup_tree_pages()
#        self._setup_view_restrictions()
#        self.client.logout()
#        # fresh login
#        # user 1 is member of group_b_access_page_and_children
#        login_ok = self.client.login(username='user_1', password='user_1')
#        self.assertEqual(login_ok , True)
#        # call /
#        url = self.get_pages_root()
#        response = self.client.get(url)
#        self.assertEqual(response.status_code, 200)
#        
#        self.assertContains( response, "href=\"/en/\"" )
#        self.assertContains( response, "href=\"/en/page_b/\"" )
#        self.assertContains( response, "href=\"/en/page_b/page_b_a/\"" )
#        # no access to page d so render it
#        self.assertNotContains( response, "href=\"/en/page_d/\"" )
#        
#        page_to_check = Page.objects.get(title_set__title= "page_b_a")
#        is_restricted = self._check_is_view_restricted_check(page_to_check)
#        # verified - the page has a view restriction
#        self.assertEquals(is_restricted, True)
#        
#        page_to_check = Page.objects.get(title_set__title= "page_b")
#        is_restricted = self._check_is_view_restricted_check(page_to_check)
#        # verified - the page has a view restriction
#        self.assertEquals(is_restricted, True)
#        
#        
#        url ="/en/"
#        self._check_url_page_found(url)
#        #page b has page and children restricted - group 1
#        url ="/en/page_b/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_a/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_b/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_b/page_b_b_a/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_b/page_b_b_b/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_b/page_b_b_c/"
#        self._check_url_page_found(url)
#        #page b_b children restricted - group 2
#        #page b_b page and descendants restricted - group 3
#        #page b_b descendants restricted - group 4
#        
#        url ="/en/page_b/page_b_c/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_d/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_d/page_b_d_a/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_d/page_b_d_b/"
#        self._check_url_page_found(url)
#        url ="/en/page_b/page_b_d/page_b_d_c/"
#        self._check_url_page_found(url)
#        
#        # no restrictions
#        url ="/en/page_c/"
#        self._check_url_page_found(url)
#        
#        ##
#        # menu entry /en/page_d for some reason
#        ##
#        # page_d has an restriction applied,
#        # the current user has no access to it
#        page_to_check = Page.objects.get(title_set__title= "page_d")
#        is_restricted = self._check_is_view_restricted_check(page_to_check)
#        # verified - the page has a view restriction
#        self.assertEquals(is_restricted, True)
#        url = "/en/page_d/"
#        self._check_url_page_not_found(url)
#        
#        # this page/menuentry belongs to another group - should not be shown here
#        ##@FIXME: this page_b has a view restriction for another group than group d
#        self.assertNotContains( response, "href=\"/en/page_d/\"" )
#        #page d page restricted - group 5
#        url ="/en/page_d/"
#        self._check_url_page_not_found(url)
#        # as the page_d is restricted and 
#        # but not the children
#        url = "/en/page_d/page_d_a/"
#        self._check_url_page_found(url)
#        url = "/en/page_d/page_d_b/"
#        self._check_url_page_found(url)
#        url = "/en/page_d/page_d_c/"
#        self._check_url_page_found(url)
#        url = "/en/page_d/page_d_d/"
#        self._check_url_page_found(url)
        
        
        
#    def test_access_page_group_d(self):
#        """
#        simulate behaviour of group d member
#        group_d_ACCESS_PAGE
#        
#        """
#        self._setup_user_groups()
#        self._setup_tree_pages()
#        self._setup_view_restrictions()
#        self.client.logout()
#        # fresh login
#        # user 1 is member of group_b_access_page_and_children
#        login_ok = self.client.login(username='user_5', password='user_5')
#        self.assertEqual(login_ok , True)
#        # call /
#        url = self.get_pages_root()
#        response = self.client.get(url)
#        self.assertEqual(response.status_code, 200)
#        
#        self.assertContains( response, "href=\"/en/\"" )
#        
#        page_to_check = Page.objects.get(title_set__title= "page_d")
#        is_restricted = self._check_is_view_restricted_check(page_to_check)
#        # verified - the page has a view restriction
#        self.assertEquals(is_restricted, True)
#        
#        ##@FIXME: this page_b has a view restriction for another group than group d
#        self.assertNotContains( response, "href=\"/en/page_b/\"" )
#        self.assertNotContains( response, "href=\"/en/page_b/page_b_a/\"" )
#        
#        #page b has page and children restricted - group 1
#        url ="/en/page_b/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_a/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_b/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_b/page_b_b_a/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_b/page_b_b_b/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_b/page_b_b_c/"
#        self._check_url_page_not_found(url)
#        #page b_b children restricted - group 2
#        #page b_b page and descendants restricted - group 3
#        #page b_b descendants restricted - group 4
#        
#        url ="/en/page_b/page_b_c/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_d/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_d/page_b_d_a/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_d/page_b_d_b/"
#        self._check_url_page_not_found(url)
#        url ="/en/page_b/page_b_d/page_b_d_c/"
#        self._check_url_page_not_found(url)
#        
#        # no restrictions
#        url ="/en/page_c/"
#        self._check_url_page_found(url)
#        
#        ##
#        # the first call contains menu entry /en/page_d for some reason
#        ##
#        # page_d has an restriction applied,
#        # but the current user has no access to it
#        page_to_check = Page.objects.get(title_set__title= "page_d")
#        is_restricted = self._check_is_view_restricted_check(page_to_check)
#        # verified - the page has a view restriction
#        self.assertEquals(is_restricted, True)
#        url = "/en/page_d/"
#        self._check_url_page_found(url)
#        
#        # this page/menuentry belongs to another group - should not be shown here
#        self.assertContains( response, "href=\"/en/page_d/\"" )
#        #page d page restricted - group 5
#        url ="/en/page_d/"
#        self._check_url_page_found(url)
#        # as the page_d is restricted and 
#        # but not the children
#        url = "/en/page_d/page_d_a/"
#        self._check_url_page_found(url)
#        url = "/en/page_d/page_d_b/"
#        self._check_url_page_found(url)
#        url = "/en/page_d/page_d_c/"
#        self._check_url_page_found(url)
#        url = "/en/page_d/page_d_d/"
#        self._check_url_page_found(url)