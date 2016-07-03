# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from cms.api import create_page
from cms.cms_menus import get_visible_pages
from cms.models import Page
from cms.models import ACCESS_DESCENDANTS, ACCESS_CHILDREN, ACCESS_PAGE
from cms.models import ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE_AND_DESCENDANTS
from cms.models.permissionmodels import GlobalPagePermission, PagePermission
from cms.test_utils.testcases import CMSTestCase
from cms.utils.page_permissions import user_can_view_page

from menus.menu_pool import menu_pool


__all__ = [
    'ViewPermissionTreeBugTests',
    'ViewPermissionComplexMenuAllNodesTests'
]


class ViewPermissionTests(CMSTestCase):
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
        | |- Page_c_a
        | |- Page_c_b
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

    def setUp(self):
        self.site = Site()
        self.site.pk = 1
        super(ViewPermissionTests, self).setUp()

    def tearDown(self):
        super(ViewPermissionTests, self).tearDown()

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

        page_c_a = create_page("page_c_a", parent=page_c, **stdkwargs)
        page_c_b = create_page("page_c_b", parent=page_c, **stdkwargs)

        page_d_a = create_page("page_d_a", parent=page_d, **stdkwargs)
        page_d_b = create_page("page_d_b", parent=page_d, **stdkwargs)
        page_d_c = create_page("page_d_c", parent=page_d, **stdkwargs)
        page_d_d = create_page("page_d_d", parent=page_d, **stdkwargs)

        pages = [
            page_a,
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
            page_c_a,
            page_c_b,
            page_d,
            page_d_a,
            page_d_b,
            page_d_c,
            page_d_d,
        ]

        new_pages = []
        for page in pages:
            new_pages.append(page.reload())
        return new_pages

    def _setup_user_groups(self):
        """
        Setup a group for every grant on ACCESS TYPE
        """
        userdata = [
            ('user_1', True, self.GROUPNAME_1),
            ('user_1_nostaff', False, self.GROUPNAME_1),
            ('user_2', True, self.GROUPNAME_2),
            ('user_2_nostaff', False, self.GROUPNAME_2),
            ('user_3', True, self.GROUPNAME_3),
            ('user_3_nostaff', False, self.GROUPNAME_3),
            ('user_4', True, self.GROUPNAME_4),
            ('user_4_nostaff', False, self.GROUPNAME_4),
            ('user_5', True, self.GROUPNAME_5),
            ('user_5_nostaff', False, self.GROUPNAME_5),
            ('user_staff', True, None),
        ]
        default_users_count = get_user_model().objects.all().count()
        for username, is_staff, groupname in userdata:
            user = self._create_user(username, is_staff)
            if groupname:
                group, _ = Group.objects.get_or_create(name=groupname)
                user_set = getattr(group, 'user_set')
                user_set.add(user)
                group.save()

        self.assertEqual(11, get_user_model().objects.all().count()-default_users_count)

    def _setup_view_restrictions(self):
        """
        Setup a view restriction with every type of the grant_on ACCESS_*
        """
        data = [("page_b", self.GROUPNAME_1, ACCESS_PAGE_AND_CHILDREN),
            ("page_b_b", self.GROUPNAME_2, ACCESS_CHILDREN),
            ("page_b", self.GROUPNAME_3, ACCESS_PAGE_AND_DESCENDANTS),
            ("page_b_b", self.GROUPNAME_4, ACCESS_DESCENDANTS),
            ("page_d", self.GROUPNAME_5, ACCESS_PAGE),
        ]
        for title, groupname, inherit in data:
            page = Page.objects.drafts().get(title_set__title=title)
            group = Group.objects.get(name__iexact=groupname)
            PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=inherit)

        self.assertEqual(5, PagePermission.objects.all().count())
        self.assertEqual(0, GlobalPagePermission.objects.all().count())

    def assertPageFound(self, url, client=None):
        if not client:
            client = self.client
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def assertPageNotFound(self, url, client=None):
        if not client:
            client = self.client
        response = client.get(url)
        self.assertEqual(response.status_code, 404)

    def assertViewAllowed(self, page, user):
        self.assertTrue(user_can_view_page(user, page))

    def assertViewNotAllowed(self, page, user):
        self.assertFalse(user_can_view_page(user, page))

    def assertInMenu(self, page, user):
        request = self.get_request(user, page)
        menu_renderer = menu_pool.get_renderer(request)
        nodes = menu_renderer.get_nodes()
        target_url = page.get_absolute_url()
        found_in_menu = False
        for node in nodes:
            if node.get_absolute_url() == target_url:
                found_in_menu = True
                break
        self.assertTrue(found_in_menu)

    def assertNotInMenu(self, page, user):
        request = self.get_request(user, page)
        menu_renderer = menu_pool.get_renderer(request)
        nodes = menu_renderer.get_nodes()
        target_url = page.get_absolute_url()
        found_in_menu = False
        for node in nodes:
            if node.get_absolute_url() == target_url:
                found_in_menu = True
                break
        self.assertFalse(found_in_menu)

    def assertNodeMemberships(self, visible_page_ids, restricted_pages, public_page_ids):
        """
        test all visible page ids are either in_public and not in_restricted
        or not in_public and in_restricted
        """
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

    def assertGrantedVisibility(self, all_pages, expected_granted_pages, username=None):
        """
        helper function to check the expected_granted_pages are
        not in the restricted_pages list and
        all visible pages are in the expected_granted_pages
        """
        # log the user in if present
        user = None
        if username is not None:
            if get_user_model().USERNAME_FIELD == 'email':
                username = username + '@django-cms.org'

            query = dict()
            query[get_user_model().USERNAME_FIELD+'__iexact'] = username
            user = get_user_model().objects.get(**query)
        request = self.get_request(user)
        visible_page_ids = get_visible_pages(request, all_pages, self.site)
        public_page_ids = Page.objects.drafts().filter(title_set__title__in=expected_granted_pages).values_list('id',
                                                                                                                flat=True)
        self.assertEqual(len(visible_page_ids), len(expected_granted_pages))
        restricted_pages = Page.objects.public().exclude(title_set__title__in=expected_granted_pages).values_list('id',
                                                                                                                  flat=True)
        self.assertNodeMemberships(visible_page_ids, restricted_pages, public_page_ids)

    def get_request(self, user=None, page=None):
        # see tests/menu.py line 753
        path = "/"
        if page:
            path = page.get_absolute_url()
        attrs = {
            'user': user or AnonymousUser(),
            'REQUEST': {},
            'POST': {},
            'GET': {},
            'path': path,
            'session': {},
        }
        return type('Request', (object,), attrs)

    def get_url_dict(self, pages, language='en'):
        return dict((page.get_absolute_url(language=language), page) for page in pages)


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='all',
)
class ViewPermissionComplexMenuAllNodesTests(ViewPermissionTests):
    """
    Test CMS_PUBLIC_FOR=all group access and menu nodes rendering
    """

    def test_public_pages_anonymous_norestrictions(self):
        """
        All pages are visible to an anonymous user
        """
        all_pages = self._setup_tree_pages()
        request = self.get_request()
        visible_page_ids = get_visible_pages(request, all_pages, self.site)
        self.assertEqual(len(all_pages), len(visible_page_ids))
        menu_renderer = menu_pool.get_renderer(request)
        nodes = menu_renderer.get_nodes()
        self.assertEqual(len(nodes), len(all_pages))

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
            'page_c_a',
            'page_c_b',
            'page_d_a',
            'page_d_b',
            'page_d_c',
            'page_d_d'
        ]
        self.assertGrantedVisibility(all_pages, granted)
        urls = self.get_url_dict(all_pages)
        user = AnonymousUser()
        request = self.get_request(user, urls['/en/'])
        menu_renderer = menu_pool.get_renderer(request)
        nodes = menu_renderer.get_nodes()
        self.assertEqual(len(nodes), 4)
        self.assertInMenu(urls["/en/"], user)
        self.assertInMenu(urls["/en/page_c/"], user)
        self.assertInMenu(urls["/en/page_c/page_c_a/"], user)
        self.assertInMenu(urls["/en/page_c/page_c_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertNotInMenu(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertNotInMenu(urls["/en/page_d/"], user)


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
            'page_c_a',
            'page_c_b',
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
        urls = self.get_url_dict(all_pages)

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_1@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_1')

        self.assertGrantedVisibility(all_pages, granted, username='user_1')
        self.assertViewAllowed(urls["/en/page_b/"], user)
        self.assertInMenu(urls["/en/page_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertInMenu(urls["/en/page_b/page_b_b/"], user)
        # descendant
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertNotInMenu(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        # group 5
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertNotInMenu(urls["/en/page_d/"], user)
        # should be public as only page_d is restricted
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)
        self.assertNotInMenu(urls["/en/page_d/page_d_a/"], user)

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
            'page_c_a',
            'page_c_b',
            'page_b_b_a',
            'page_b_b_b',
            'page_b_b_c',
            # not restricted
            'page_d_a',
            'page_d_b',
            'page_d_c',
            'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_2')
        urls = self.get_url_dict(all_pages)

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_2@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_2')

        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/page_b_b_a_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_menu_access_page_and_descendants_group_3(self):
        """
        simulate behaviour of group 3 member
        group_b_ACCESS_PAGE_AND_DESCENDANTS to page_b
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
            'page_c_a',
            'page_c_b',
            'page_d_a',
            'page_d_b',
            'page_d_c',
            'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_3')
        urls = self.get_url_dict(all_pages)

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_3@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_3')

        self.assertViewAllowed(urls["/en/page_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_d/page_b_d_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_menu_access_descendants_group_4(self):
        """
        simulate behaviour of group 4 member
        group_b_b_ACCESS_DESCENDANTS to page_b_b
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
            'page_c_a',
            'page_c_b',
            'page_d_a',
            'page_d_b',
            'page_d_c',
            'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_4')
        urls = self.get_url_dict(all_pages)

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_4@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_4')

        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewNotAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_menu_access_page_group_5(self):
        """
        simulate behaviour of group b member
        group_d_ACCESS_PAGE to page_d
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        self._setup_view_restrictions()
        granted = ['page_a',
            'page_c',
            'page_c_a',
            'page_c_b',
            'page_d',
            'page_d_a',
            'page_d_b',
            'page_d_c',
            'page_d_d',
        ]
        self.assertGrantedVisibility(all_pages, granted, username='user_5')
        urls = self.get_url_dict(all_pages)

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_5@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_5')

        # call /
        self.assertViewNotAllowed(urls["/en/page_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/"], user)
        self.assertViewNotAllowed(urls["/en/page_b/page_b_b/page_b_b_a/"], user)
        self.assertViewAllowed(urls["/en/page_d/"], user)
        self.assertViewAllowed(urls["/en/page_d/page_d_a/"], user)

    def test_non_view_permission_doesnt_hide(self):
        """
        PagePermissions with can_view=False shouldn't hide pages in the menu.
        """
        self._setup_user_groups()
        all_pages = self._setup_tree_pages()
        page = Page.objects.drafts().get(title_set__title="page_b")
        group = Group.objects.get(name=self.GROUPNAME_1)
        PagePermission.objects.create(can_view=False, group=group, page=page)
        urls = self.get_url_dict(all_pages)
        self.assertInMenu(urls["/en/page_b/"], AnonymousUser())


@override_settings(
    CMS_PERMISSION=True,
    CMS_PUBLIC_FOR='all',
)
class ViewPermissionTreeBugTests(ViewPermissionTests):
    """Test issue 1113
    https://github.com/divio/django-cms/issues/1113
    Wrong view permission calculation in PagePermission.objects.for_page
    grant_on=ACCESS_PAGE_AND_CHILDREN or ACCESS_PAGE_AND_DESCENDANTS to page 6
    Test if this affects the menu entries and page visibility
    """
    GROUPNAME_6 = 'group_6_ACCESS_PAGE'

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
        user = self._create_user('user_6', True)
        group = Group.objects.create(name=self.GROUPNAME_6)
        user_set = getattr(group, 'user_set')
        user_set.add(user)
        group.save()

    def _setup_permviewbug(self):
        """
        Setup group_6_ACCESS_PAGE view restriction
        """
        page = Page.objects.drafts().get(title_set__title="page_6")
        group = Group.objects.get(name__iexact=self.GROUPNAME_6)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE_AND_CHILDREN)
        PagePermission.objects.create(can_view=True, group=group, page=page, grant_on=ACCESS_PAGE_AND_DESCENDANTS)

    def test_pageforbug(self):
        all_pages = self._setup_pages()
        self._setup_user()
        self._setup_permviewbug()
        for page in all_pages:
            perm = PagePermission.objects.for_page(page=page)
            # only page_6 has a permission assigned
            if page.get_title() == 'page_6':
                self.assertEqual(len(perm), 2)
            else:
                msg = "Permission wrong at page %s" % (page.get_title())
                self.assertEqual(len(perm), 0, msg)
        granted = ['page_1',
            'page_2',
            'page_3',
            'page_4',
            'page_5',
        ]
        urls = self.get_url_dict(all_pages)
        user = AnonymousUser()
        # anonymous doesn't see page_6
        self.assertGrantedVisibility(all_pages, granted)
        self.assertViewAllowed(urls["/en/page_2/page_3/page_4/"], user)
        self.assertViewAllowed(urls["/en/page_5/"], user)
        self.assertViewNotAllowed(urls["/en/page_5/page_6/"], user)
        # group member
        granted = ['page_1',
            'page_2',
            'page_3',
            'page_4',
            'page_5',
            'page_6',
        ]

        self.assertGrantedVisibility(all_pages, granted, username='user_6')

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.get(email='user_6@django-cms.org')
        else:
            user = get_user_model().objects.get(username='user_6')
        url = "/en/page_2/page_3/page_4/"
        self.assertViewAllowed(urls[url], user)
        url = "/en/page_5/page_6/"
        self.assertViewAllowed(urls[url], user)
